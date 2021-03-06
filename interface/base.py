import os
import subprocess


class NotImplementedInterface(Exception):
    pass

class Interface(object):

    def __init__(self, path, name, searchengine=None):
        self.path = path
        self.name = name
        self.searchengine = searchengine

    def do_commit(self, filenames):
        raise NotImplementedInterface

    def get(self, filename):
        raise NotImplementedInterface

    def getraw(self, filename):
        raise NotImplementedInterface

    def add(self, filename, filedata):
        raise NotImplementedInterface

    def exists(self, filename):
        raise NotImplementedInterface

    def modify(self, filename, filedata):
        raise NotImplementedInterface

    def lsfiles(self):
        raise NotImplementedInterface

    def search(self, keywords, path='', files=None):
        if self.searchengine is None:
            result = self.grep(keywords, path=path, files=files)
        else:
            result = self.SEsearch(keywords)
        return result

    def search_yaml(self, keywords, path='', files=None):
        if self.searchengine is None:
            result = self.grep_yaml(keywords, path=path, files=files)
        else:
            result = self.SEsearch_yaml(keywords)
        return result

    def grep(self):
        raise NotImplementedInterface

    def grep_yaml(self):
        raise NotImplementedInterface

    def SEsearch(self, keywords):
        indexname = '.'.join([self.name])
        keyword_list = list()
        for keyword in keywords.split():
            keyword_list.append({"match":
                            {"content": {"query": keyword, "analyzer": "ik_max_word"}}})
        result = self.searchengine.search(index=indexname, size=500, _source_include="file",
            body={"query": {
                    "bool": {
                        "must": keyword_list
                        }
                    }
                }, request_timeout=30)
        return set(map(lambda x: (os.path.splitext(x['_source']['file']['filename'])[0],
                                  x['_score']), result['hits']['hits']))

    def SEsearch_yaml(self, keywords):
        indexname = '.'.join([self.name, 'yaml'])
        keyword_list = list()
        for keyword in keywords.split():
            keyword_list.append({"match":
                            {"content": {"query": keyword, "analyzer": "ik_max_word"}}})
        result = self.searchengine.search(index=indexname, size=500, _source_include="file",
            body={"query": {
                    "bool": {
                        "must": keyword_list
                        }
                    }
                }, request_timeout=30)
        return set(map(lambda x: (os.path.splitext(x['_source']['file']['filename'])[0],
                                  x['_score']), result['hits']['hits']))

    def subprocess_grep(self, command, path, shell):
        grep_list = []
        greppath = os.path.join(self.repo.path, path)
        if not os.path.exists(greppath):
            return grep_list
        p = subprocess.Popen(command,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT,
                             cwd=greppath, shell=shell)
        returncode = p.communicate()[0]
        for each in returncode.split('\n'):
            if each:
                grep_list.append((each, 1))
        return grep_list

    def delete(self):
        raise NotImplementedInterface
