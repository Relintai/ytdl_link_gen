from __future__ import unicode_literals
import os
from os.path import exists
import yt_dlp
from yt_dlp.utils import sanitize_filename

from yt_dlp.utils import PagedList
from yt_dlp.utils import LazyList
from yt_dlp.utils import itertools
from yt_dlp.utils import EntryNotInPlaylist
from yt_dlp.utils import url_basename
from yt_dlp.utils import get_domain
from yt_dlp.utils import sanitize_url

import re
import json
import sys
import datetime 
import shutil
import gc

config_data = []
video_file_data = {}


def print_usage():
    print("Usage:");
    print("index <folder list>    : Indexes folders");
    print("gen                    : generates video download shell script");
    exit()

def copy(src, dest):
    try:
        shutil.copytree(src, dest)
    except OSError as e:
        # If the error was caused because the source wasn't a directory
        if e.errno == errno.ENOTDIR:
            shutil.copy(src, dest)
        else:
            print('Directory not copied. Error: %s' % e)

def backup_data():
    t = datetime.datetime.now()
    orig_folder_name = "backups/data-" + str(t.year) + "-" + str(t.month) + "-" + str(t.day)
    folder_name = orig_folder_name

    indx = 1
    while os.path.exists(folder_name):
        folder_name = orig_folder_name + "-" + str(indx)
        indx += 1

    copy("data", folder_name)

#config.txt:
#<category / folder> <link> <data_folder> <folder> <dl params>
#data.json-> all vid name store
#command index param folder -> add all vids to data.json
#command gen -> get all list, filter based on vids.json, a.k.a if contains link str
#gens

def load_config(file):
    global config_data

    config_data = []

    if not os.path.exists(file) or not os.path.isfile(file):
        return

    f = open(file, "r")
    
    for l in f:
        if len(l) == 0 or l[0] == "#":
            continue

        ls = l.split("|")

        if len(ls) < 5:
            if l.strip() == "":
                continue

            print("load_config: skipped line: " + l)
            continue

        d = {
            "category": ls[0].strip(),
            "link": ls[1].strip(),
            "json_file_name" : ls[2].strip(),
            "result_folder" : ls[3].strip(),
            "cmdparams": ls[4].strip()
        }

        config_data.append(d)

    f.close()

def index_folders(path):
    index_folder_videos(path)

    files = os.listdir(path)

    for f in files:
        fp = path + "/" + f

        if os.path.isdir(fp):
            index_folders(fp)

def index_folder_videos(path):
    video_file_data = None

    paths = path.split("/")

    if len(paths) == 0:
        return

    ch_id = paths[len(paths) - 1]

    chdata = None

    if ch_id in video_file_data:
        chdata = video_file_data[ch_id]
    else:
        chdata = {
            "maxindex": "",
            "files": {}
        }

    fdict = chdata["files"]

    print("Indexing: " + path)

    files = os.listdir(path)

    totalcount = 0
    count = 0

    top_index_file = ""
    top_index = -1

    for f in files:
        fp = path + "/" + f

        if os.path.isdir(fp):
            continue

        #Don't index subtitles
        if f.endswith("vtt") or f.endswith("json") or f.endswith("py") or f.endswith("sh") or f.endswith("txt"):
            continue

        if not f in fdict:
            fdict[f] = 1
            count += 1

        totalcount += 1

        fs = f.split("-")

        if len(fs) == 0:
            continue

        indx = -1

        try:
            indx = int(fs[0])
        except:
            continue

        if indx > top_index:
            top_index_file = f
            top_index = indx

    if top_index != -1:
        chdata["maxindex"] = top_index_file

    video_file_data[ch_id] = chdata

    print("indexed: " + str(totalcount) + " files in total. " + str(count) + " new files.")
    


def index_folders(path):
    index_folder_videos(path)

    files = os.listdir(path)

    for f in files:
        fp = path + "/" + f

        if os.path.isdir(fp):
            index_folders(fp)

def index_folder_videos(path):
    video_file_data = None

#prog

data_file = "data.json"
config_file = "config.txt"

#if len(sys.argv) < 2:
#    print_usage()

#command = sys.argv[1]
command = "gen"

#if command != "index" and command != "gen":
#    print_usage()

backup_data()


if command == "index":
    print("INDEXING NEEDS TO BE REIMPLEMENTED!")
    exit()
    if len(sys.argv) < 3:
        print_usage()

    load_data(data_file)

    for i in range(2, len(sys.argv)):
        f = sys.argv[i]

        if not os.path.exists(f) or not os.path.isdir(f):
            print("Path doesn't exists, or not a folder: " + f)
            continue

        if f[len(f) - 1] == "/":
            f = f[0:-1]

        index_folders(f)

    save_data(data_file)

    exit()


class YTDLNew(yt_dlp.YoutubeDL):
    def __init__(self, params=None, auto_init=True):
        super().__init__(params, auto_init)

    def process_ie_result(self, ie_result, download=True, extra_info=None):
        """
        Take the result of the ie(may be modified) and resolve all unresolved
        references (URLs, playlist items).
        It will also download the videos if 'download'.
        Returns the resolved ie_result.
        """
        if extra_info is None:
            extra_info = {}
        result_type = ie_result.get('_type', 'video')

        print(result_type)

        if result_type in ('url', 'url_transparent'):
            ie_result['url'] = sanitize_url(ie_result['url'])
            if ie_result.get('original_url'):
                extra_info.setdefault('original_url', ie_result['original_url'])

            extract_flat = self.params.get('extract_flat', False)
            if ((extract_flat == 'in_playlist' and 'playlist' in extra_info)
                    or extract_flat is True):
                info_copy = ie_result.copy()
                ie = try_get(ie_result.get('ie_key'), self.get_info_extractor)
                if ie and not ie_result.get('id'):
                    info_copy['id'] = ie.get_temp_id(ie_result['url'])
                self.add_default_extra_info(info_copy, ie, ie_result['url'])
                self.add_extra_info(info_copy, extra_info)
                info_copy, _ = self.pre_process(info_copy)
                self.__forced_printings(info_copy, self.prepare_filename(info_copy), incomplete=True)
                if self.params.get('force_write_download_archive', False):
                    self.record_download_archive(info_copy)
                return ie_result

        if result_type == 'video':
            self.add_extra_info(ie_result, extra_info)
            ie_result = self.process_video_result(ie_result, download=download)
            additional_urls = (ie_result or {}).get('additional_urls')
            if additional_urls:
                # TODO: Improve MetadataParserPP to allow setting a list
                if isinstance(additional_urls, compat_str):
                    additional_urls = [additional_urls]
                self.to_screen(
                    '[info] %s: %d additional URL(s) requested' % (ie_result['id'], len(additional_urls)))
                self.write_debug('Additional URLs: "%s"' % '", "'.join(additional_urls))
                ie_result['additional_entries'] = [
                    self.extract_info(
                        url, download, extra_info=extra_info,
                        force_generic_extractor=self.params.get('force_generic_extractor'))
                    for url in additional_urls
                ]
            return ie_result
        elif result_type == 'url':
            # We have to add extra_info to the results because it may be
            # contained in a playlist
            return self.extract_info(
                ie_result['url'], download,
                ie_key=ie_result.get('ie_key'),
                extra_info=extra_info)
        elif result_type == 'url_transparent':
            # Use the information from the embedding page
            info = self.extract_info(
                ie_result['url'], ie_key=ie_result.get('ie_key'),
                extra_info=extra_info, download=False, process=False)

            # extract_info may return None when ignoreerrors is enabled and
            # extraction failed with an error, don't crash and return early
            # in this case
            if not info:
                return info

            force_properties = dict(
                (k, v) for k, v in ie_result.items() if v is not None)
            for f in ('_type', 'url', 'id', 'extractor', 'extractor_key', 'ie_key'):
                if f in force_properties:
                    del force_properties[f]
            new_result = info.copy()
            new_result.update(force_properties)

            # Extracted info may not be a video result (i.e.
            # info.get('_type', 'video') != video) but rather an url or
            # url_transparent. In such cases outer metadata (from ie_result)
            # should be propagated to inner one (info). For this to happen
            # _type of info should be overridden with url_transparent. This
            # fixes issue from https://github.com/ytdl-org/youtube-dl/pull/11163.
            if new_result.get('_type') == 'url':
                new_result['_type'] = 'url_transparent'

            return self.process_ie_result(
                new_result, download=download, extra_info=extra_info)
        elif result_type in ('playlist', 'multi_video'):
            # Protect from infinite recursion due to recursively nested playlists
            # (see https://github.com/ytdl-org/youtube-dl/issues/27833)
            webpage_url = ie_result['webpage_url']
            if webpage_url in self._playlist_urls:
                self.to_screen(
                    '[download] Skipping already downloaded playlist: %s'
                    % ie_result.get('title') or ie_result.get('id'))
                return

            self._playlist_level += 1
            self._playlist_urls.add(webpage_url)
            self._sanitize_thumbnails(ie_result)
            try:
                return self.__process_playlist(ie_result, download)
            finally:
                self._playlist_level -= 1
                if not self._playlist_level:
                    self._playlist_urls.clear()
        elif result_type == 'compat_list':
            self.report_warning(
                'Extractor %s returned a compat_list result. '
                'It needs to be updated.' % ie_result.get('extractor'))

            def _fixup(r):
                self.add_extra_info(r, {
                    'extractor': ie_result['extractor'],
                    'webpage_url': ie_result['webpage_url'],
                    'webpage_url_basename': url_basename(ie_result['webpage_url']),
                    'webpage_url_domain': get_domain(ie_result['webpage_url']),
                    'extractor_key': ie_result['extractor_key'],
                })
                return r
            ie_result['entries'] = [
                self.process_ie_result(_fixup(r), download, extra_info)
                for r in ie_result['entries']
            ]
            return ie_result
        else:
            raise Exception('Invalid result type: %s' % result_type)

    def __process_playlist(self, ie_result, download):
        # We process each entry in the playlist
        playlist = ie_result.get('title') or ie_result.get('id')
        self.to_screen('[download] Downloading playlist: %s' % playlist)

        if 'entries' not in ie_result:
            raise EntryNotInPlaylist('There are no entries')

        MissingEntry = object()
        incomplete_entries = bool(ie_result.get('requested_entries'))
        if incomplete_entries:
            def fill_missing_entries(entries, indices):
                ret = [MissingEntry] * max(indices)
                for i, entry in zip(indices, entries):
                    ret[i - 1] = entry
                return ret
            ie_result['entries'] = fill_missing_entries(ie_result['entries'], ie_result['requested_entries'])

        playlist_results = []

        playliststart = self.params.get('playliststart', 1)
        playlistend = self.params.get('playlistend')
        # For backwards compatibility, interpret -1 as whole list
        if playlistend == -1:
            playlistend = None

        playlistitems_str = self.params.get('playlist_items')
        playlistitems = None
        if playlistitems_str is not None:
            def iter_playlistitems(format):
                for string_segment in format.split(','):
                    if '-' in string_segment:
                        start, end = string_segment.split('-')
                        for item in range(int(start), int(end) + 1):
                            yield int(item)
                    else:
                        yield int(string_segment)
            playlistitems = orderedSet(iter_playlistitems(playlistitems_str))

        ie_entries = ie_result['entries']
        if isinstance(ie_entries, list):
            playlist_count = len(ie_entries)
            msg = f'Collected {playlist_count} videos; downloading %d of them'
            ie_result['playlist_count'] = ie_result.get('playlist_count') or playlist_count

            def get_entry(i):
                return ie_entries[i - 1]
        else:
            msg = 'Downloading %d videos'
            if not isinstance(ie_entries, (PagedList, LazyList)):
                ie_entries = LazyList(ie_entries)

            def get_entry(i):
                return YTDLNew._handle_extraction_exceptions(
                    lambda self, i: ie_entries[i - 1]
                )(self, i)

        entries, broken = [], False
        items = playlistitems if playlistitems is not None else itertools.count(playliststart)
        for i in items:
            if i == 0:
                continue
            if playlistitems is None and playlistend is not None and playlistend < i:
                break
            entry = None
            try:
                entry = get_entry(i)
                if entry is MissingEntry:
                    raise EntryNotInPlaylist()
            except (IndexError, EntryNotInPlaylist):
                if incomplete_entries:
                    raise EntryNotInPlaylist(f'Entry {i} cannot be found')
                elif not playlistitems:
                    break
            entries.append(entry)
            try:
                if entry is not None:
                    self._match_entry(entry, incomplete=True, silent=True)
            except (ExistingVideoReached, RejectedVideoReached):
                broken = True
                break
        ie_result['entries'] = entries

        # Save playlist_index before re-ordering
        entries = [
            ((playlistitems[i - 1] if playlistitems else i + playliststart - 1), entry)
            for i, entry in enumerate(entries, 1)
            if entry is not None]
        n_entries = len(entries)

        if not (ie_result.get('playlist_count') or broken or playlistitems or playlistend):
            ie_result['playlist_count'] = n_entries

        if not playlistitems and (playliststart != 1 or playlistend):
            playlistitems = list(range(playliststart, playliststart + n_entries))
        ie_result['requested_entries'] = playlistitems

        _infojson_written = False
        write_playlist_files = self.params.get('allow_playlist_files', True)
        if write_playlist_files and self.params.get('list_thumbnails'):
            self.list_thumbnails(ie_result)
        if write_playlist_files and not self.params.get('simulate'):
            ie_copy = self._s_playlist_infodict(ie_result, n_entries=n_entries)
            _infojson_written = self._write_info_json(
                'playlist', ie_result, self.prepare_filename(ie_copy, 'pl_infojson'))
            if _infojson_written is None:
                return
            if self._write_description('playlist', ie_result,
                                       self.prepare_filename(ie_copy, 'pl_description')) is None:
                return
            # TODO: This should be passed to ThumbnailsConvertor if necessary
            self._write_thumbnails('playlist', ie_copy, self.prepare_filename(ie_copy, 'pl_thumbnail'))

        if self.params.get('playlistreverse', False):
            entries = entries[::-1]
        if self.params.get('playlistrandom', False):
            random.shuffle(entries)

        x_forwarded_for = ie_result.get('__x_forwarded_for_ip')

        self.to_screen('[%s] playlist %s: %s' % (ie_result['extractor'], playlist, msg % n_entries))

        failures = 0
        max_failures = self.params.get('skip_playlist_after_errors') or float('inf')
        for i, entry_tuple in enumerate(entries, 1):
            playlist_index, entry = entry_tuple
            if 'playlist-index' in self.params.get('compat_opts', []):
                playlist_index = playlistitems[i - 1] if playlistitems else i + playliststart - 1
            #self.to_screen('[download] Downloading video %s of %s' % (i, n_entries))
            # This __x_forwarded_for_ip thing is a bit ugly but requires
            # minimal changes
            if x_forwarded_for:
                entry['__x_forwarded_for_ip'] = x_forwarded_for
            extra = {
                'n_entries': n_entries,
                '_last_playlist_index': max(playlistitems) if playlistitems else (playlistend or n_entries),
                'playlist_count': ie_result.get('playlist_count'),
                'playlist_index': playlist_index,
                'playlist_autonumber': i,
                'playlist': playlist,
                'playlist_id': ie_result.get('id'),
                'playlist_title': ie_result.get('title'),
                'playlist_uploader': ie_result.get('uploader'),
                'playlist_uploader_id': ie_result.get('uploader_id'),
                'extractor': ie_result['extractor'],
                'webpage_url': ie_result['webpage_url'],
                'webpage_url_basename': url_basename(ie_result['webpage_url']),
                'webpage_url_domain': get_domain(ie_result['webpage_url']),
                'extractor_key': ie_result['extractor_key'],
            }

            if self._match_entry(entry, incomplete=True) is not None:
                continue

            #entry_result = self._YoutubeDL__process_iterable_entry(entry, download, extra)
            entry_result = self.process_ie_result_force_nodl(entry, False, extra)
            if not entry_result:
                failures += 1
            if failures >= max_failures:
                self.report_error(
                    'Skipping the remaining entries in playlist "%s" since %d items failed extraction' % (playlist, failures))
                break
            playlist_results.append(entry_result)
        ie_result['entries'] = playlist_results

        # Write the updated info to json
        if _infojson_written and self._write_info_json(
                'updated playlist', ie_result,
                self.prepare_filename(ie_copy, 'pl_infojson'), overwrite=True) is None:
            return

        #ie_result = self.s_run_all_pps('playlist', ie_result)
        self.to_screen(f'[download] Finished downloading playlist: {playlist}')
        return ie_result

    def process_ie_result_force_nodl(self, ie_result, download=True, extra_info=None):
        self.add_extra_info(ie_result, extra_info)

        #ie_result = self.process_video_result(ie_result, download=download)
        #additional_urls = (ie_result or {}).get('additional_urls')
        #if additional_urls:
        #    # TODO: Improve MetadataParserPP to allow setting a list
        #    if isinstance(additional_urls, compat_str):
        #        additional_urls = [additional_urls]
        #    self.to_screen(
        #        '[info] %s: %d additional URL(s) requested' % (ie_result['id'], len(additional_urls)))
        #    self.write_debug('Additional URLs: "%s"' % '", "'.join(additional_urls))
        #    ie_result['additional_entries'] = [
        #        self.extract_info(
        #            url, download, extra_info=extra_info,
        #            force_generic_extractor=self.params.get('force_generic_extractor'))
        #        for url in additional_urls
        #    ]
        return ie_result

    def s_run_all_pps(self, key, info, *, additional_pps=None):
        for tmpl in self.params['forceprint'].get(key, []):
            self._s_forceprint(tmpl, info)

        for pp in (additional_pps or []) + self._pps[key]:
            info = self.s_run_pp(pp, info)

        return info


    def s_run_pp(self, pp, infodict):
        files_to_delete = []
        if '__files_to_move' not in infodict:
            infodict['__files_to_move'] = {}
        try:
            files_to_delete, infodict = pp.run(infodict)
        except PostProcessingError as e:
            # Must be True and not 'only_download'
            if self.params.get('ignoreerrors') is True:
                self.report_error(e)
                return infodict
            raise

        if not files_to_delete:
            return infodict
        if self.params.get('keepvideo', False):
            for f in files_to_delete:
                infodict['__files_to_move'].setdefault(f, '')
        else:
            for old_filename in set(files_to_delete):
                self.to_screen('Deleting original file %s (pass -k to keep)' % old_filename)
                try:
                    os.remove(encodeFilename(old_filename))
                except (IOError, OSError):
                    self.report_warning('Unable to remove downloaded original file')
                if old_filename in infodict['__files_to_move']:
                    del infodict['__files_to_move'][old_filename]
        return infodict

    def _s_forceprint(self, tmpl, info_dict):
        mobj = re.match(r'\w+(=?)$', tmpl)
        if mobj and mobj.group(1):
            tmpl = f'{tmpl[:-1]} = %({tmpl[:-1]})r'
        elif mobj:
            tmpl = '%({})s'.format(tmpl)

        info_dict = info_dict.copy()
        info_dict['formats_table'] = self.render_formats_table(info_dict)
        info_dict['thumbnails_table'] = self.render_thumbnails_table(info_dict)
        info_dict['subtitles_table'] = self.render_subtitles_table(info_dict.get('id'), info_dict.get('subtitles'))
        info_dict['automatic_captions_table'] = self.render_subtitles_table(info_dict.get('id'), info_dict.get('automatic_captions'))
        self.to_stdout(self.evaluate_outtmpl(tmpl, info_dict))

    @staticmethod
    def _s_playlist_infodict(ie_result, **kwargs):
        return {
            **ie_result,
            'playlist': ie_result.get('title') or ie_result.get('id'),
            'playlist_id': ie_result.get('id'),
            'playlist_title': ie_result.get('title'),
            'playlist_uploader': ie_result.get('uploader'),
            'playlist_uploader_id': ie_result.get('uploader_id'),
            'playlist_index': 0,
            **kwargs,
        }

class ChannelEntry:
    category = ""
    link = "link"
    json_file_name = ""
    result_folder = ""
    cmdparams = ""

    base_folder = ""
    data_file = ""
    temp_data_file = ""
    video_output_dir = ""
    output_command_data_file = ""

    max_index = 0
    pad_to = -1
    
    video_file_data = None


    def parse_config_line(self, l):
        #d = {
        #    "category": ls[0].strip(),
        #    "link": ls[1].strip(),
        #    "json_file_name" : ls[2].strip(),
        #    "result_folder" : ls[3].strip(),
        #    "cmdparams": ls[4].strip()
        #}

        self.category = l["category"]
        self.link = l["link"]
        self.json_file_name = l["json_file_name"]
        self.result_folder = l["result_folder"]
        self.cmdparams = l["cmdparams"]

        self.base_folder = "data/" + self.category
        self.data_file = self.base_folder + "/" + self.json_file_name + ".json"

        if not os.path.exists("data/" + self.category):
            os.makedirs("data/" + self.category)

        self.temp_data_file = "temp/" + self.category + "/" + self.json_file_name + "_yt.json"

        if not os.path.exists("temp/" + self.category):
            os.makedirs("temp/" + self.category)

        self.video_output_dir = self.category + "/" + self.result_folder


        #if not os.path.exists(self.video_output_dir):
        #    os.makedirs(self.video_output_dir)

        #self.output_command_data_file = "result/" + self.category + "/dl.sh"
        self.output_command_data_file = "dl.sh"

    def load_data(self):
        if not os.path.exists(self.data_file) or not os.path.isfile(self.data_file):

            self.max_index = 0
            self.pad_to = -1

            self.video_file_data = {
                "maxindex": "",
                "files": {}
            }

            return

        with open(self.data_file, "r") as f:
            self.video_file_data = json.load(f)

        max_index_str = self.video_file_data["maxindex"]
        self.max_index = 0
        self.pad_to = -1

        if max_index_str != "":
            ms = max_index_str.split("-")

            if len(ms) != 0:
                try:
                    self.max_index = int(ms[0])
                    self.pad_to = len(ms[0])
                except:
                    pass

    def save_data(self):
        f = open(self.data_file, "w")
        
        f.write(json.dumps(self.video_file_data))

        f.close()

    def unload_data(self):
        self.video_file_data = None

    def yt(self):
        ydl_opts = {
            'ignoreerrors': True,
            "playlistreverse": True
        }

        data = None

        if exists(self.temp_data_file):
            with open(self.temp_data_file) as f:
                data = json.load(f)

            return data

        with YTDLNew(ydl_opts) as ydl:
            data = ydl.extract_info(self.link, False)

            f = open(self.temp_data_file, "w")
            f.write(json.dumps(data))
            f.close()

        #print(data)

        return data

    def process(self):
        self.load_data()

        videos_links = []
        data = self.yt()

        es = data["entries"]

        selected_data = []

        files = self.video_file_data["files"]

        for e in es:
            if not isinstance(e, dict):
                continue

            #check if we have it
            found = False
            for fk in files.keys():
                if e["id"] in fk:
                    found = True
                    break

            if found:
                continue

            #need
            fns = ""

            if "title" in e:
                fns = sanitize_filename(e["title"], True)

            arr = {
                "id": e["id"],
                "sanitized_title": fns,
                "playlist_index": e["playlist_index"],
                "url": e["url"]
            }

            selected_data.append(arr)

        if len(selected_data) == 0:
            return

        selected_data.sort(key=lambda x: x["playlist_index"], reverse=True)

        if self.pad_to == -1:
            self.pad_to = len(str(len(files) + len(selected_data)))

        command_outfile = open(self.output_command_data_file, "a")

        main_fname = ""
        for s in selected_data:
            self.max_index += 1

            #-o '%(playlist_index)s-%(title)s-%(id)s.%(ext)s'
            main_fname = str(self.max_index).zfill(self.pad_to) + "-" + s["sanitized_title"] + "-" + s["id"]

            print("New video: " + main_fname)

            files[main_fname] = 1

            url_escaped = s["url"].replace("'", "\\'")
            url_escaped = url_escaped.replace('"', '\\"')

            command = "yt-dlp " + l["cmdparams"] + " -o './" + self.video_output_dir + "/" + main_fname + ".%(ext)s' " + url_escaped

            command_outfile.write(command + "\n")

        command_outfile.close()

        if main_fname != "":
            self.video_file_data["maxindex"] = main_fname
            
        self.video_file_data["files"] = files
        self.save_data()


if command == "gen":
    load_config(config_file)

    for l in config_data:
        ce = ChannelEntry()
        ce.parse_config_line(l)
        ce.process()
        ce.unload_data()

        ce = None

        collected = gc.collect()
        print("Garbage collector: collected", "%d objects." % collected)
