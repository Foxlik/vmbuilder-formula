# -*- coding: utf-8 -*-
# vim: sts=4 ts=4 sw=4 et ai
import salt.exceptions

class VmbuilderException(Exception):
     def __init__(self, value):
         self.value = value
     def __str__(self):
         return repr(self.value)

def chroot_command_on_host(commands):
    """
    Function get dict and start, command on host 
    for changes prev create vm host
    """
    import uuid
    command =' && '.join(commands)
    tmpConfigFilename = "/tmp/"+str(uuid.uuid4())
    postInstallScript = """#!/bin/bash
    chroot $1 /bin/bash -c '{0} && exit'""".format(command)

    comdat = __salt__['file.write'](tmpConfigFilename, postInstallScript)
    comdat = __salt__['file.set_mode'](tmpConfigFilename, 755)
    return tmpConfigFilename

def installed (
    name,
    os='ubuntu',
    release='trusty',
    hostname='vm1',
    domain='defaultdomain',
    arch="amd64",
    addToLibvirt=True,
    mirror=False, # mirror, that will be placed in vm apt conf
    installMirror=False, # mirror only for installation process
    installMinion=True,
    hdddriver="virtio",
    mgmtiface="eth0",
    proxy=False,
    network={},
    disks=[],
    autostart=False,
    saltmaster="saltmaster01"):

    name = ' '.join(name.strip().split())
    ret = {'name': name,
    'result': False,
    'changes': {},
    'comment': ''}
    try:
        # check if vm is already exists
        checkcmd = __salt__['cmd.run_all']("/usr/bin/virsh list --all | grep -w {0}".format(hostname), python_shell=True)
        if not checkcmd['retcode']:
            ret['result'] = True
            return ret

        # check if it test mode
        if __opts__["test"] ==  True:
            return ret

        # vmbuilder required
        if not __salt__['pkg.version']("ubuntu-vm-builder"):
            inst = __salt__['pkg.install']("ubuntu-vm-builder")
            ret['changes']['ubuntu-vm-builder'] = inst

        if hdddriver == "virtio":
            cpresult = __salt__['cp.get_file']('salt://_states/libvirtxml.tmpl', '/etc/vmbuilder/libvirt/libvirtxml.tmpl')
            ret['changes']['copy-tmpl-virtio'] = cpresult

        # create config script
        execes = set(["echo \\\"master: {0}\\\" > /etc/salt/minion".format(saltmaster)])
        if hdddriver == "virtio":
            execes.add("""echo \\\"proc                                            /proc           proc    defaults        0       0
/dev/vda1                                       /               ext4    defaults        0       0
/dev/vda2                                       swap            swap    defaults        0       0 \\\" > /etc/fstab""")
            execes.add("""sed -i.bak s/sda1/vda1/g /boot/grub/menu.lst""")
        
        #create iface vlan
        if mgmtiface != "eth0":
            execes.add("""echo \\\"auto {0} 
  iface {0} inet dhcp
  vlan-raw-device eth0
  pre-up ifconfig eth0 up\\\" >> /etc/network/interfaces""".format(mgmtiface))

        # Удаляем предыдущий вариант vm
        comdat = __salt__['cmd.run_all']("virsh destroy {0} && virsh undefine {0}".format(hostname), python_shell=True)
        if comdat['retcode']:
            ret['changes']['If exists, destroying previous vm with the same name'] = "Failed: {0}".format(comdat['stderr'])
        else:
            ret['changes']['If exists, destroying previous vm with the same name'] = 'Ok. ' + comdat['stdout']

        # create command
        cmd = "vmbuilder kvm"
        cmd += ' ' + os
        cmd += " --suite {0}".format(release)
        cmd += " --flavour virtual" # ставим систему оптимизированную под виртуалки
        cmd += " --arch {0}".format(arch)
        cmd += " -o" # overwrite vm with the same name
        if (addToLibvirt): cmd += " --libvirt qemu:///system"
        cmd += " --hostname {0}".format(hostname)
        cmd += " --domain {0}".format(domain)
        if (mirror):
            cmd += " --mirror {0}".format(mirror)
            cmd += " --security-mirror {0}".format(mirror)
        elif (installMirror):
            cmd += " --install-mirror {0}".format(installMirror)
            cmd += " --install-security-mirror {0}".format(installMirror)
        if (proxy):
            cmd += " --proxy {0}".format(proxy)
        cmd += " --addpkg linux-image-generic" # иначе flavour virtual не работает
        if (installMinion):
            if __grains__['osrelease'] < 14.04 :
                cmd += " --addpkg=python-software-properties" # нужно салту
            else:
                cmd += " --addpkg=software-properties-common" # нужно салту (ubuntu 14.04)
            cmd += " --addpkg=python-apt" # нужно салту для установки пакетов
            cmd += " --addpkg=openssh-server" # нужно салту для установки пакетов
            cmd += " --ppa=saltstack/salt" # ставим ppa для salt
            cmd += " --addpkg=salt-minion" # ставим сразу salt-minion на виртуалку
            cmd += " --addpkg=vlan"
            cmd += " --exec \"{0}\"".format(chroot_command_on_host(execes)) # выполняем скрипт после установки

        # networking
        if network[0]:
            cmd += " --bridge {0}".format(network[0]['hyperv_dev'])

        # discs
        discchar = ord('a');
        adddiskcmd = []
        for disk in disks:
            rootsize = None
            swapsize = None
            try:
                rootsize = disk['rootsize']
                swapsize = disk['swapsize']
            except KeyError:
                pass
            if (rootsize or swapsize) and discchar != ord('a'):
                ret['comment'] = "Swap and root must be on the first device, it's vmbuilder restriction. If you want it on different devices, you can add device to vm using thismodule, and then configure fstab on vm after installation using some other module."
                return ret;
            if rootsize:
                cmd += " --raw {0}".format(disk['device'])
                cmd += " --rootsize {0}".format(rootsize)
                if swapsize:
                    cmd += " --swapsize {0}".format(swapsize)
            else:
                adddiskcmd.append("/usr/bin/virsh attach-disk {0} {1} {2} --persistent --driver qemu --subdriver raw".format(hostname,disk['device'], 'hd'+chr(discchar)));
            discchar = discchar + 1

        ret['changes']['Vmbuilder command is'] = cmd
        #ret['result'] = True
        comdat = __salt__['cmd.run_all'](cmd)

        if comdat['retcode']:
            ret['result'] = False
            ret['comment'] = "Vmbuilder run error: {0}".format(comdat['stderr'])
            return ret
        else:
            ret['changes']['Vmbuilder command result'] = 'Ok. ' + comdat['stdout']

        # networking
        i = 0
        for netw in network:
            if (i > 0):
                comdat = __salt__['cmd.run_all']("/usr/bin/virsh attach-interface {0} --type bridge --source {1} --persistent".format(hostname,netw['hyperv_dev']))
                if comdat['retcode']:
                    ret['result'] = False
                    ret['comment'] = "Add interface failed: {0}".format(comdat['stderr'])
                    return ret
                else:
                    ret['changes']["Add interface {0}".format(netw['hyperv_dev'])] = 'Ok. ' + comdat['stdout']
            i = i + 1

        for diskcmd in adddiskcmd:
            comdat = __salt__['cmd.run_all'](diskcmd)
            if comdat['retcode']:
                ret['comment'] = "Add disk failed: {0}".format(comdat['stderr'])
                return ret
            else:
                ret['changes']["Add disk: {0}".format(diskcmd)] = 'Ok. ' + comdat['stdout']

        # autostart
        if autostart:
            comdat = __salt__['cmd.run_all']("virsh autostart {0} && virsh start {0}".format(hostname))
            if comdat['retcode']:
                ret['result'] = False
                ret['comment'] = "Autostart setting failed: {0}".format(comdat['stderr'])
                return ret
            else:
                ret['changes']['Autostart setting'] = 'Ok. ' + comdat['stdout']

        ret['result'] = True    
        return ret
    except VmbuilderException as e:
        ret['result'] = False
        ret['comment'] = e.value
        return ret
 
