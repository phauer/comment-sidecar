import re
from conftest import get_file_path

# plain text parsing, so the check needs no PHP


def read(path):
    return get_file_path(path).read_text()


def constants(source):
    return set(re.findall(r'^const (\w+) =', source, re.MULTILINE))


def site_option_keys(source):
    sites = source[source.index('const SITES'):source.index('const DEFAULT_SITE')]
    entries = re.split(r'^    "[^"]+" => \[', sites, flags=re.MULTILINE)[1:]
    return [set(re.findall(r'^        "(\w+)" =>', entry, re.MULTILINE)) for entry in entries]


def test_example_config_defines_the_same_constants_as_the_dev_config():
    assert constants(read('deploy/config.example.php')) == constants(read('src/config.php'))


def test_example_sites_have_the_same_options_as_the_dev_sites():
    dev_keys = site_option_keys(read('src/config.php'))[0]
    example_sites = site_option_keys(read('deploy/config.example.php'))
    assert len(example_sites) >= 1
    for keys in example_sites:
        assert keys == dev_keys


def test_deploy_env_example_defines_the_variables_the_script_requires():
    script = read('deploy/deploy.sh')
    required = re.search(r'\$\{SSH_TARGET:\?\}.*', script).group(0)
    example = read('deploy/deploy.example.env')
    for name in re.findall(r'\$\{(\w+):\?\}', required):
        assert re.search(rf'^{name}=', example, re.MULTILINE), name


def test_examples_contain_no_real_hosts():
    for path in ['deploy/config.example.php', 'deploy/deploy.example.env']:
        for domain in re.findall(r'https?://([\w.-]+)', read(path)):
            assert domain.endswith('example.com') or domain.endswith('example.de'), (path, domain)
