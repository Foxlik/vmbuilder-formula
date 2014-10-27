# -*- coding: utf-8 -*-
import salt.exceptions

def format (
	name,
	fstype='ext4'
):

	ret = {'name': name,
		'result': False,
		'changes': {},
		'comment': ''}
	
	# check if it test mode
	if __opts__["test"] ==  True:
		pass
	
	# check already formatted
	
	# psutil required
	if not __salt__['pkg.version']("python-psutil"):
		inst = __salt__['pkg.install']("python-psutil")
		ret['changes']['psutils'] = inst
	
	checkcmd = __salt__['cmd.run_all']("blkid -o value -s TYPE {0}".format(name))
	if not checkcmd['retcode']:
		ret['comment'] = "{0} is already formatted as {1}".format(name, checkcmd['stdout'])
		if checkcmd['stdout'] == fstype:
			ret['result'] = True
		else:
			ret['result'] = False
		return ret
	
	# device not found on host, error
	cmd = __salt__['extfs.mkfs'](name, fstype)
	ret['changes']['mkfs'] = cmd
	if cmd:
		ret['result'] = True
		ret['comment'] = 'Mkfs complete successfull'
	else:
		ret['result'] = False
		ret['comment'] = "Device {0} not found on minion".format(name)
	return ret
