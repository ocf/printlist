import yaml
from types import SimpleNamespace

def deepNamespace(dictionary):
	for key in dictionary:
		if isinstance(dictionary[key], dict):
			dictionary[key] = deepNamespace(dictionary[key])
	return SimpleNamespace(**dictionary)

def Config(*filenames):
	with open('conf/default.yaml', 'r') as stream:
		Configuration = yaml.safe_load(stream)
	for filename in filenames:
		with open(filename, 'r') as stream:
			Configuration.update(yaml.safe_load(stream))
	return deepNamespace(Configuration)