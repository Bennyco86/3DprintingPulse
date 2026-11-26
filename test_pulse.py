import datetime
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

import auto_daily as a
import generate_rss as rss


class PulseRegressionTests(unittest.TestCase):
    def test_images_in_content_and_lazy_markup(self):
        node = ET.fromstring('<item xmlns:c="urn:content"><c:encoded><![CDATA['
                             '<img src="data:image/gif;base64,x" data-src="/hero.webp">'
                             ']]></c:encoded></item>')
        self.assertEqual(a.extract_image_from_element(node, 'https://publisher.test/story'),
                         'https://publisher.test/hero.webp')

    def test_metadata_attribute_order_and_entities(self):
        markup = '<meta content="/hero.jpg?a=1&amp;b=2" property="og:image">'
        self.assertEqual(a.extract_html_image(markup, 'https://publisher.test/story', True),
                         'https://publisher.test/hero.jpg?a=1&b=2')
        self.assertEqual(a.extract_html_image('<img src="/logo.png">', 'https://p.test', True), '')

    def test_new_model_and_distinct_models(self):
        for title in ('Bambu Lab launches H3C with nine tools', 'Tool changer: Bambu Lab presents H3C'):
            self.assertEqual(a.major_release_signature_from_text(title), 'bambu:h3c')
        self.assertEqual(a.major_release_signature_from_text('Bambu Lab reveals H30C'), 'bambu:h30c')
        self.assertNotEqual(a.major_release_signature_from_text('Bambu Lab H3C Pro'), 'bambu:h3c')

    def test_history_keeps_long_titles_ending_in_period(self):
        title = 'Bambu Lab launches H3C ' + 'with new capabilities ' * 10 + '.'
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp, '2026-11-05')
            folder.mkdir()
            (folder / 'README.md').write_text('# Quality3Ds Daily News\n\n## Stories\n\n'
                + title + '\nSummary.\nRead more ? https://p.test/h3c\n', encoding='utf-8')
            history = a.load_seen_story_history(tmp)
            self.assertIn('bambu:h3c', history['major_signatures'])
            item = dict(title='Bambu Lab unveils H3C tool-changing printer', summary='',
                        url='https://other.test/launch', source='TCT Magazine',
                        published=datetime.datetime.now(datetime.timezone.utc))
            self.assertEqual(a.select_stories([item], history), [])
            item['title'] = 'Bambu Lab H3C nine-tool printer specifications'
            self.assertEqual(a.select_stories([item], history), [])

    def test_launch_not_blocked_by_earlier_teaser(self):
        teasers = ['Bambu Lab teases its first 3D scanner, the S1 3D, for November 2026 launch',
                   "Bambu Lab S1: FCC Approval Marks Bambu Lab's First Portable 3D Scanner",
                   'Bambu Lab launches S1 3D scanner, opening sign-ups for early access']
        with tempfile.TemporaryDirectory() as tmp:
            for day, title in zip(('2026-10-13', '2026-10-14', '2026-10-19'), teasers):
                folder = Path(tmp, day)
                folder.mkdir()
                (folder / 'README.md').write_text('# Pulse\n\n## Stories\n\n' + title
                    + '\nSummary.\nRead more ? https://p.test/' + day + '\n', encoding='utf-8')
            history = a.load_seen_story_history(tmp)
            self.assertIn('bambu:s1', history['prelaunch_signatures'])
            self.assertNotIn('bambu:s1', history['major_signatures'])
            now = datetime.datetime.now(datetime.timezone.utc)
            launch = dict(title='Easy in Hand, Pro in Every Scan: Bambu Lab introduces the S1 3D scanner',
                          summary='', url='https://p.test/launch', source='Bambu Lab', published=now)
            self.assertEqual(len(a.select_stories([launch], history)), 1)
            teaser = dict(title='Bambu Lab S1 scanner spotted ahead of launch', summary='',
                          url='https://p.test/leak', source='Bambu Lab', published=now)
            self.assertEqual(a.select_stories([teaser], history), [])
            archive = 'Bambu Lab introduces the S1 3D scanner\nDetails.\nRead more ? https://p.test/launch'
            self.assertEqual(rss.filter_archive_repeats(archive, history), archive)
            self.assertIn('bambu:s1', history['major_signatures'])
            relaunch = 'Bambu Lab launches S1 scanner\nDetails.\nRead more ? https://p.test/again'
            self.assertEqual(rss.filter_archive_repeats(relaunch, history), '')

    def test_same_model_across_categories_in_one_run(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        items = [dict(title=title, summary='', url='https://p.test/' + str(i),
                      source='TCT Magazine', published=now)
                 for i, title in enumerate(['Bambu Lab launches H3C desktop printer',
                                            'Tool changer: Bambu Lab H3C nine-tool printer specifications'])]
        self.assertEqual(len(a.select_stories(items, set())), 1)

    def test_public_archive_omits_repeated_model_preserving_new_story(self):
        history = dict(urls=set(), title_signatures=set(), title_topic_tokens=set(), major_signatures=set())
        original = 'Bambu Lab launches H3C\nDetails.\nRead more ? https://p.test/a'
        self.assertEqual(rss.filter_archive_repeats(original, history), original)
        later = 'Bambu Lab unveils H3C nine-tool printer\nDetails.\nRead more ? https://p.test/b'
        fresh = 'A novel medical implant design\nDetails.\nRead more ? https://p.test/c'
        self.assertEqual(rss.filter_archive_repeats(later + '\n\n' + fresh, history), fresh)

    def test_unconditional_304_is_retried(self):
        import urllib.error
        error = urllib.error.HTTPError('https://p.test/feed', 304, 'Not Modified', {}, None)
        response = unittest.mock.MagicMock()
        response.__enter__.return_value = response
        response.read.return_value = b'<rss/>'
        response.geturl.return_value = 'https://p.test/feed'
        with patch.object(a.urllib.request, 'urlopen', side_effect=[error, response]) as request, patch.object(a.time, 'sleep'):
            self.assertEqual(a.fetch_bytes('https://p.test/feed')[0], b'<rss/>')
            self.assertIn('_pulse=', request.call_args.args[0].full_url)


if __name__ == '__main__':
    unittest.main()
