import sys
import yaml

templates = list(sys.argv[1:])

errors = []
end_template={'HeatTemplateFormatVersion': '2012-12-12',
              'Description': []}
for template_path in templates:
    template = yaml.safe_load(open(template_path))
    end_template['Description'].append(template.get('Description',
                                                    template_path))
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

    new_outputs = template.get('Outputs', {})
    for o, obody in iter(new_outputs.items()):
        if o in end_template.get('Outputs', {}):
            if pbody != end_template['Outputs'][p]:
                errors.append('Output %s from %s conflicts.' % (o,
                                                                   template_path))
            continue
        if 'Outputs' not in end_template:
            end_template['Outputs'] = {}
        end_template['Outputs'][o] = obody

    new_resources = template.get('Resources', {})
    for r, rbody in iter(new_resources.items()):
        if rbody['Type'] == 'AWS::EC2::Instance':
            # XXX Assuming ImageId is always a Ref
            del end_template['Parameters'][rbody['Properties']['ImageId']['Ref']]
            role = rbody.get('Metadata', {}).get('OpenStack::Role', r)
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
            ikey = '%sImage' % (role)
            end_template['Resources'][role]['Properties']['ImageId'] = {'Ref': ikey}
            end_template['Parameters'][ikey] = {'Type': 'String'}
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
end_template['Description'] = ','.join(end_template['Description'])
sys.stdout.write(yaml.safe_dump(end_template, default_flow_style=False))
