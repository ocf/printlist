import yaml
from attrdict import AttrDict

def Config(*filenames):
	with open('conf/default.yaml', 'r') as stream:
		Configuration = yaml.safe_load(stream)
	for filename in filenames:
		with open(filename, 'r') as stream:
			Configuration.update(yaml.safe_load(stream))
	return AttrDict(Configuration)