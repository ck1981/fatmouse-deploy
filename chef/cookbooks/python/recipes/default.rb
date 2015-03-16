# install python 3.3.5
apt_repository 'deadsnakes' do
    uri 'http://ppa.launchpad.net/fkrull/deadsnakes/ubuntu'
    distribution 'precise'  # hardcode for debian wheezy
    components ['main']
    keyserver 'keyserver.ubuntu.com'
    key 'DB82666C' 
end 
package "python3.3-dev"
package "python3.3-dbg"

# install pip
bash "ensure pip" do
    cwd "/tmp"
    code <<-EOS
        curl -L https://bootstrap.pypa.io/get-pip.py | python3.3
        EOS
    not_if "which pip3.3"
end

execute "pip3.3 install flask"
