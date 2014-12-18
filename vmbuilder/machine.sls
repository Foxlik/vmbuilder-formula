# vim: sts=2 ts=2 sw=2 expandtab autoindent
{% set vmbuilderall = salt['pillar.get']('vmbuilder') %}

{% for vmname,vmbuilder in vmbuilderall.iteritems() %}
{%- if vmbuilder.get("name") %}

{%- for lvitem in vmbuilder.get("lvm", []) %}
{%- for devitem in lvitem.devices %}
{{ devitem  ~ '_' ~ vmbuilder.get("name") ~ '_' ~ loop.index0 }}:
  lvm.pv_present:
    - name: {{ devitem }}
{% endfor %}
{{ lvitem.vgname  ~ '_' ~ vmbuilder.get("name") }}:
  lvm.vg_present:
    - name: {{ lvitem.vgname }}
    - devices:
    {%- for devitem in lvitem.devices %}
      - {{ devitem }} 
    {%- endfor %}
{% endfor %}

{{ vmbuilder.get("name") }}:
  kvm:
    - installed
    - autostart: True
    - os: ubuntu
    - release: {{ vmbuilder.get("release","trusty") }}
    - hostname: {{ vmbuilder.get("name","") }}
    - domain: {{ vmbuilder.get("domain","") }} 
    {%- if vmbuilder.get("saltmaster")  %}
    - saltmaster: {{ vmbuilder.get("saltmaster","saltmaster01") }} 
    {%- endif %}
    {%- if vmbuilder.get("mgmtiface")  %}
    - mgmtiface: {{ vmbuilder.get("mgmtiface","eth0") }}
    {%- endif %}
    - network:
    {%- for netitem in vmbuilder.get("network", []) %}
        - dev: {{ netitem.dev }} 
          mode: {{ netitem.mode }}
          hyperv_dev: {{ netitem.hyperv }} 
    {%- endfor %}
    - disks:
    {%- for diskitem in vmbuilder.get("disks", []) %}
        - device: /dev/{{ vmbuilder.get("vgname") }}/{{ diskitem.lvname | default(vmbuilder.get("name")) }}
          rootsize: {{ diskitem.rootsize | default("30000") }} 
          swapsize: {{ diskitem.swapsize | default("2000") }} 
    {%- endfor %}
    {%- if vmbuilder.get("proxy")  %}
    - proxy: {{ vmbuilder.get("proxy") }}
    {% endif %}
    - require:
      - lvm: {{ vmbuilder.get("name","") }}_root
{% for diskitem in vmbuilder.get("disks", []) %}
{{ diskitem.lvname | default(vmbuilder.get("name")) }}: 
  lvm.lv_present:
    - vgname: {{ vmbuilder.get("vgname") }}
    - size: {{ diskitem.allsize }} 
    - require:
      - lvm: {{ vmbuilder.get("vgname") }}
{% endfor %}
{% endif %}
{% endfor %}
