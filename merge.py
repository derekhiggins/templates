import sys
import yaml
import uuid

templates = list(sys.argv[1:])

errors = []
end_template={}
for template_path in templates:
    template = yaml.safe_load(open(template_path))
    new_parameters = template.get('Parameters', {})
    for p, pbody in iter(new_parameters.items()):
        if p in end_template.get('Parameters', {}):
            if pbody != end_template['Parameters'][p]:
                errors.append('Parameter %s from %s conflicts.' % (p,
                                                                   template_path))
            continue
        if 'Parameters' not in end_template:
            end_template['Parameters'] = {}
        end_template['Parameters'][p] = pbody
    new_resources = template.get('Resources', {})
    for r, rbody in iter(new_resources.items()):
        if rbody['Type'] == 'AWS::EC2::Instance':
            role = rbody.get('Metadata', {}).get('OpenStack::Role',
                                                 str(uuid.uuid1()))
            if role in end_template.get('Resources', {}):
                new_metadata = rbody.get('Metadata', {})
                for m, mbody in iter(new_metadata.items()):
                    if m in end_template['Resources'][role].get('Metadata', {}):
                        if m == 'OpenStack::ImageBuilder::Elements':
                            end_template['Resources'][role]['Metadata'][m].extend(mbody)
                            continue
                        if mbody != end_template['Resources'][role]['Metadata'][m]:
                            errors.append('Role %s metadata key %s conflicts.' %
                                          (role, m))
                        continue
                    end_template['Resources'][role]['Metadata'][m] = mbody
                continue
            if 'Resources' not in end_template:
                end_template['Resources'] = {}
            end_template['Resources'][role] = rbody
            #end_template['Resources'][role]['Properties']['ImageId'] = {'Ref': '%sImage' % role}
        else:
            if r in end_template.get('Resources', {}):
                if rbody != end_template['Resources'][r]:
                    errors.append('Resource %s from %s conflicts' % (r,
                                                                     template_path))
                continue
            if 'Resources' not in end_template:
                end_template['Resources'] = {}
            end_template['Resources'][r] = rbody

            
if errors:
    for e in errors:
        sys.stderr.write("ERROR: %s\n" % e)
print yaml.safe_dump(end_template, default_flow_style=False)
