from mozlog import structured
from mozrunner import LocalRunner
from manifestparser import TestManifest

import corredor
import json
import os
import subprocess

here = os.path.abspath(os.path.dirname(__file__))

def write_manifest():
    manifest = TestManifest(['manifest.ini'])

    active_paths = [t['path'] for t in manifest.active_tests(disabled=False)]
    blacklist = [t for t in manifest.paths() if t not in active_paths]
    with open('manifest.json', 'w') as f:
        f.writelines(json.dumps(blacklist, indent=2))

def run_gaia_integration():
    cwd = os.path.abspath(os.path.join(here, '../../../'))
    print cwd
    command = ['make', 'test-integration', 'REPORTER=mocha-tbpl-reporter', 'TEST_MANIFEST=./tests/python/runner-service/manifest.json']
    subprocess.Popen(command, cwd=cwd)


write_manifest()
run_gaia_integration()

output = corredor.OutputHandler('ipc', '/tmp/corredor_worker_output')
output.process_output()

worker = corredor.ExclusivePair('ipc', '/tmp/corredor_exclusivepair')
results = []

def setup_application(profile):
    # use profile to launch b2g_desktop/device
    worker.send_json({'action': 'ready'})

def teardown_application():
    pass

def on_profile(data):
    profile = data['profile']
    print 'received profile: %s' % profile
    setup_application(profile)

def on_test_end(data):
    results.append(data)
    teardown_application()


# register callback on profile action
worker.register_action('profile', on_profile)
worker.register_action('test_end', on_test_end)
worker.wait_for_action('fin')
worker.cleanup()

print 'Test results: %s' % json.dumps(results, indent=2)
print 'stdout:\n%s' % ''.join(output.stdout)
print 'stderr:\n%s' % ''.join(output.stderr)

