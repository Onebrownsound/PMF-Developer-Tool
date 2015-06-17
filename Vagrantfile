Vagrant.configure("2") do |config|
  config.vm.box ="lucid32"
  config.vm.provision :shell, path: "bootstrap.sh"
  config.vm.provider "virtualbox" do |v|
    v.gui = true
  end

end