execute "apt-get update"

package "nodejs"
package "npm"

execute "install our app" do
    cwd "/opt"
    command "npm install"
end
