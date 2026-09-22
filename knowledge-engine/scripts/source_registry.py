import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_FILE = PROJECT_ROOT / 'knowledge-engine' / 'config' / 'source_registry.json'


def load_registry():
    with open(REGISTRY_FILE, 'r', encoding='utf-8-sig') as file:
        return json.load(file)


def get_file_sources():
    return load_registry().get('file_sources', {})


def get_web_sources():
    return load_registry().get('web_sources', {})


def find_type_by_extension(extension):
    extension = extension.lower().strip()
    if not extension.startswith('.'):
        extension = '.' + extension
    registry = load_registry()
    for source_name, source in registry.get('file_sources', {}).items():
        extensions = {x.lower().strip() for x in source.get('extensions', [])}
        if extension in extensions:
            return source_name, source
    return 'unknown', registry.get('unknown_source', {})


def find_web_source(url):
    url = url.lower().strip()
    registry = load_registry()

    for source_name, source in registry.get('web_sources', {}).items():
        if source_name == 'generic_url':
            continue

        schemes = source.get('schemes', [])
        domains = source.get('domains', [])

        if not schemes and not domains:
            continue

        if schemes and not any(url.startswith(scheme + ':') for scheme in schemes):
            continue

        if domains and not any(domain in url for domain in domains):
            continue

        return source_name, source

    generic = registry.get('web_sources', {}).get('generic_url')
    if generic:
        schemes = generic.get('schemes', [])
        if not schemes or any(url.startswith(scheme + ':') for scheme in schemes):
            return 'generic_url', generic

    return 'unknown', registry.get('unknown_source', {})
