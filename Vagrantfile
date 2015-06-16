Vagrant.configure("2") do |config|
  config.vm.box ="Windows_Xp"
  config.vm.provision :shell, path: "bootstrap.sh"
  config.vm.provider "virtualbox" do |v|
    v.gui = true
  end

end