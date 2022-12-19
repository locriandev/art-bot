from unittest.mock import patch, MagicMock

from flexmock import flexmock
import pytest

from artbotlib import buildinfo
from tests.util import OutputInspector


@patch('artbotlib.util.please_notify_art_team_of_error')
@pytest.mark.asyncio
async def test_get_image_info(_):
    inspector = OutputInspector()

    # Fake CI image
    res = await buildinfo.get_image_info(
        inspector, 'ironic', 'registry.ci.openshift.org/ocp/release:4.11.0-0.ci.2022-12-19-155547')
    assert res == (None, None, None)
    assert 'Sorry, no ART build info for a CI image.' in inspector.output

    # Image not in quay.io or registry.ci.openshift.org
    res = await buildinfo.get_image_info(
        inspector, 'ironic', 'registry-proxy.engineering.redhat.com/rh-osbs/'
                             'openshift-ose-ironic:v4.12.0-202212191555.p0.g2a90d95.assembly.stream')
    assert res == (None, None, None)
    assert 'Sorry, I can only look up pullspecs for quay.io or registry.ci.openshift.org' in inspector.output

    # Simulate failure in 'oc adm release info'
    with patch('artbotlib.exectools.cmd_gather_async') as mock:
        inspector.reset()
        mock.return_value = 1, '', ''
        res = await buildinfo.get_image_info(
            inspector, 'ironic', 'quay.io/openshift-release-dev/ocp-release:4.12.0-ec.5-x86_64')
        assert res == (None, None, None)
        assert "Sorry, I wasn't able to query the release image pullspec" in inspector.output[0]

    # Simulate invalid JSON returned by 'oc adm release info'
    with patch('artbotlib.exectools.cmd_gather_async') as mock:
        inspector.reset()
        mock.return_value = 0, '', ''
        res = await buildinfo.get_image_info(
            inspector, 'ironic', 'quay.io/openshift-release-dev/ocp-release:4.12.0-ec.5-x86_64')
        assert res == (None, None, None)
        assert "Sorry, I wasn't able to decode the JSON info for pullspec" in inspector.output[0]

    # Finally, let's check the returned release image text
    with patch('artbotlib.exectools.cmd_gather_async') as mock:
        mock.return_value = 0, '{}', '{}'
        _, _, release_img_text = await buildinfo.get_image_info(
            inspector, 'ironic', 'quay.io/openshift-release-dev/ocp-release:4.12.0-ec.5-x86_64')
        assert release_img_text == \
            '<docker://quay.io/openshift-release-dev/ocp-release:4.12.0-ec.5-x86_64|ocp-release:4.12.0-ec.5-x86_64>'


@patch('artbotlib.buildinfo.get_image_info')
def test_buildinfo_for_release_rhcos(get_image_info_mock):
    """
    Test 'artbotlib.buildinfo.buildinfo_for_release' for machine-os-content
    """

    mock = flexmock(buildinfo)

    rhcos_build_info = {
        "config": {
            "config": {
                "Hostname": "c07ed41fe7ec",
                "Labels": {
                    "version": "v4.10.0"
                }
            },
            'architecture': 'amd64'
        }
    }

    get_image_info_mock.return_value = rhcos_build_info, '', ''

    mock.should_receive('rhcos_build_urls').once().with_args(
        rhcos_build_info["config"]["config"]["Labels"]["version"],
        rhcos_build_info["config"]["architecture"]
    ).and_return(None, None)

    mock.buildinfo_for_release(MagicMock(), 'machine-os-content', '4.10')
