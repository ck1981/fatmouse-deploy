import os
import json
from string import Template
from tempfile import NamedTemporaryFile, TemporaryDirectory

from invoke import task, run

PROJECT_ID = json.loads(run("gcloud config list project --format json").stdout)['core']['project']


@task
def release():
    docker_repo = "gcr.io/{}/flask-test".format(PROJECT_ID.replace('-', '_'))
    commit_hash = run("git rev-parse HEAD").stdout.strip()
    run("docker build -t {}:{} .".format(docker_repo, commit_hash))
    run("gcloud preview docker push {}:{}".format(docker_repo, commit_hash))
    print("Successfully released container: {}".format(commit_hash))


@task
def deploy(cluster, config, release, version):
    bucket_name = "gs://deployment_{}".format(PROJECT_ID)
    environ = os.environ.copy()
    environ.update({'FAM_DEPLOY_RELEASE_VERSION': release,
                    'FAM_DEPLOY_VERSION': version})
    with open(config) as src, NamedTemporaryFile(mode="w+") as tmp:
        result = Template(src.read()).safe_substitute(environ)
        tmp.write(result)
        tmp.flush()

        r = run("gsutil ls {}".format(bucket_name), warn=True)
        if not r.ok:
            # Create the bucket if it's the frist deploy
            run("gsutil mb {}".format(bucket_name))

        run("gsutil cp {src} {bucket_name}/{cluster}/{version}/{config}".format(
            src=tmp.name, bucket_name=bucket_name, cluster=cluster,
            version=version, config=config))
    print("Successfully pushed deploy: {}".format(version))


@task
def delivery(cluster_name, deploy_version):
    bucket_name = "gs://deployment_{}".format(PROJECT_ID)
    metadata_path = "{}/{}/metadata".format(bucket_name, cluster_name)

    deploy_configs = "{bucket_name}/{cluster_name}/{deploy_version}/*".format(
        bucket_name=bucket_name, cluster_name=cluster_name, deploy_version=deploy_version)

    with TemporaryDirectory() as tmpdirname:
        run("gsutil cp {configs} {tmp}".format(configs=deploy_configs, tmp=tmpdirname))
        config_files = (os.path.join(tmpdirname, config) for config in os.listdir(tmpdirname))

        metadata = run("gsutil cat {}".format(metadata_path), warn=True)
        current_version = metadata.stdout.strip() if metadata.ok else None

        for config in config_files:
            if current_version:
                controller_name = os.path.basename(config).split('.')[0]
                current_controller = "{}-{}".format(controller_name, current_version)
                command = "gcloud preview container kubectl rollingupdate {current_controller} -f {new_controller} --update-period=5s".format(
                    current_controller=current_controller, new_controller=config)
                run(command)
            else:
                # First deploy on a fresh cluster
                run("gcloud preview container kubectl create -f {}".format(config))

    with NamedTemporaryFile(mode="w+") as tmp:
        tmp.write(deploy_version)
        tmp.flush()

        run("gsutil cp {} {}".format(tmp.name, metadata_path))

    print("Successfully delivered version: {}".format(deploy_version))
