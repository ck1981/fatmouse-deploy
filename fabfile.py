import os
import json
import shutil
import tempfile
from string import Template
from tempfile import NamedTemporaryFile

from fabric.api import task, local
from fabric.context_managers import settings

PROJECT_ID = json.loads(local("gcloud config list project --format json", capture=True))['core']['project']


@task
def release():
    repo_root = "gcr.io/{}".format(PROJECT_ID.replace('-', '_'))
    commit_hash = local("git rev-parse HEAD", capture=True).strip()
    tmpdir = os.path.join(tempfile.mkdtemp(), os.path.basename(os.path.realpath(os.curdir)))

    shutil.copytree('.', tmpdir)

    confdir = os.path.join(tmpdir, 'config')
    configs = ((os.path.join(confdir, name), name) for name in os.listdir(confdir))
    for (path, name) in configs:
        dockerfile = os.path.join(path, 'Dockerfile')
        repo_name = "{}/{}:{}".format(repo_root, name, commit_hash)
        shutil.copy(dockerfile, tmpdir)
        local("docker build -t {} {}".format(repo_name, tmpdir))
        local("gcloud preview docker push {}".format(repo_name))
        print("Successfully released container: {}".format(repo_name))


@task
def deploy(cluster, release, version):
    bucket_name = "gs://deployment_{}".format(PROJECT_ID)
    # Create the bucket on the frist deploy
    with settings(warn_only=True):
        r = local("gsutil ls {}".format(bucket_name))
        if r.failed:
            local("gsutil mb {}".format(bucket_name))

    environ = os.environ.copy()
    environ.update({'FAM_DEPLOY_RELEASE_VERSION': release,
                    'FAM_DEPLOY_VERSION': version})

    tmpdir = tempfile.mkdtemp()
    configs = ((os.path.join(os.path.realpath('./config'), name), name) for name in os.listdir('./config'))

    for (path, name) in configs:
        config_name = "{}-controller.json".format(name)
        template = os.path.join(path, config_name)
        config = os.path.join(tmpdir, config_name)
        with open(template) as tmpl, open(config, 'w+') as cfg:
            result = Template(tmpl.read()).safe_substitute(environ)
            cfg.write(result)

        local("gsutil cp {src} {bucket_name}/{cluster}/{version}/{config}".format(
            src=config, bucket_name=bucket_name, cluster=cluster,
            version=version, config=config_name))
    print("Successfully pushed deploy: {}".format(version))


@task
def delivery(cluster_name, deploy_version):
    bucket_name = "gs://deployment_{}".format(PROJECT_ID)
    metadata_path = "{}/{}/metadata".format(bucket_name, cluster_name)

    deploy_configs = "{bucket_name}/{cluster_name}/{deploy_version}/*".format(
        bucket_name=bucket_name, cluster_name=cluster_name, deploy_version=deploy_version)

    tmpdirname = tempfile.mkdtemp()
    local("gsutil cp {configs} {tmp}".format(configs=deploy_configs, tmp=tmpdirname))
    config_files = (os.path.join(tmpdirname, config) for config in os.listdir(tmpdirname))

    with settings(warn_only=True):
        metadata = local("gsutil cat {}".format(metadata_path), capture=True)
        current_version = metadata.strip() if not metadata.failed else None

    for config in config_files:
        if current_version:
            controller_name = os.path.basename(config).split('.')[0]
            current_controller = "{}-{}".format(controller_name, current_version)
            command = "gcloud preview container kubectl rollingupdate {current_controller} -f {new_controller} --update-period=5s".format(
                current_controller=current_controller, new_controller=config)
            local(command)
        else:
            # First deploy on a fresh cluster
            local("gcloud preview container kubectl create -f {}".format(config))

    with NamedTemporaryFile(mode="w+") as tmp:
        tmp.write(deploy_version)
        tmp.flush()

        local("gsutil cp {} {}".format(tmp.name, metadata_path))

    print("Successfully delivered version: {}".format(deploy_version))
