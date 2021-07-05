import sys
import yaml

MANDATORY_ARGS = ['port', 'config']
MANDATORY_LABELS = ['app_name', 'env']

def create_settings_file(args):
    # Making sure all mandatory flags are there in command
    argument_keys = []
    argument_values = []
    for i, x in enumerate(args):
        if i%2 == 0:
            # x[2:] to remove --
            argument_keys.append(x[2:])
        else:
            argument_values.append(x)
    try:
        arguments = {k:v for k, v in zip(argument_keys, argument_values)}
        for x in MANDATORY_ARGS:
            if x not in arguments:
                raise Exception('Argument missing')
    except Exception as e:
        print('Error: Not a valid command')
        return 0

    # Creating settings file from yml filte
    with open(arguments['config'], 'r') as stream:
        try:
            yaml_config = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            return 0
    try:
        settings_dict = {}
        # Checking mandatory labels
        for backend in yaml_config['backends']:
            match_labels = [ml.split('=')[0] for ml in backend['match_labels']]
            for x in MANDATORY_LABELS:
                if x not in match_labels:
                    raise Exception('Match label missing')
            settings_dict[backend['name']] = {}

        for route in yaml_config['routes']:
            settings_dict[route['backend']]['path_prefix'] = route['path_prefix']

        default_error_code = yaml_config['default_response']['status_code']
        default_error_message = yaml_config['default_response']['body']
    except Exception as e:
        print('Error: Not a valid config')
        return 0

    # Creating settings file
    with open('rgate/local_settings.py', 'w') as fp:
        settings_vars = '''PORT = %s\nBACKENDS = %s\nDEFAULT_ERROR_CODE = %s\nDEFAULT_ERROR_MESSAGE = '%s' ''' % \
            (arguments['port'], settings_dict, default_error_code, default_error_message)
        fp.write(settings_vars)


if __name__ == '__main__':
    print('Inside python script')
    create_settings_file(sys.argv[1:])
