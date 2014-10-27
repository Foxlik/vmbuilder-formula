#
# vim: sts=2 ts=2 sw=2 expandtab autoindent
kvm:
  pkg.installed:
    - pkgs:
      - qemu-kvm
      - libvirt-bin
      - virtinst
      # fore network bridge
      - bridge-utils
      # for network bondings
      - ifenslave
      - vlan
