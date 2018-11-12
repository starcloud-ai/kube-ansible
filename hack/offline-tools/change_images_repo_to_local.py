#!/usr/bin/env python

import re
import argparse

repo_pattern = [
    "(^ *)image: *k8s.gcr.io/(.*)",
    "(^ *)image: *gcr.io/(.*)",
    "(^ *)baseImage: *quay.io/(.*)",
    "(^ *)image: *quay.io/(.*)",
    "(^ *)- *image: *quay.io/(.*)",
    "(^ *)image: *docker.io/(.*)",
    "(^ *)image: *docker.elastic.co/(.*)",
    "(^ *)image: *registry.opensource.zalan.do/(.*)",
    "(^.*)=quay.io/coreos/(.*$)",
    "(^ *)image: *(.*)",
    "(^ *)- *image: *(.*)",
]

new_repo_format = {
    "(^ *)image: *k8s.gcr.io/(.*)": "%simage: %s/%s\n",
    "(^ *)image: *gcr.io/(.*)": "%simage: %s/%s\n",
    "(^ *)baseImage: *quay.io/(.*)": "%sbaseImage: %s/%s\n",
    "(^ *)image: *quay.io/(.*)": "%simage: %s/%s\n",
    "(^ *)- *image: *quay.io/(.*)": "%s- image: %s/%s\n",
    "(^ *)image: *docker.io/(.*)": "%simage: %s/%s\n",
    "(^ *)image: *docker.elastic.co/(.*)": "%simage: %s/%s\n",
    "(^.*)=quay.io/coreos/(.*$)": "%s=%s/coreos/%s\n",
    "(^ *)image: *registry.opensource.zalan.do/(.*)": "%simage: %s/%s\n",
    "(^ *)image: *(.*)": "%simage: %s/%s\n",
    "(^ *)- *image: *(.*)": "%s- image: %s/%s\n",
}

repo_pattern_obj = {}


def process_line(file, line, repo):
    if repo in line:
        return False, line

    for p in repo_pattern:
        regex_obj, needprocess = repo_pattern_obj[p]
        match_obj = regex_obj.match(line)
        if match_obj and needprocess:
            return True, new_repo_format[p] % (match_obj.groups()[0], repo, match_obj.groups()[1])
        elif match_obj and not needprocess:
            return False, line
    return False, line


def process_file(filename, repo):
    content = []
    newcontent = []
    needbackup = False

    with open(filename) as istream:
        content = istream.readlines()

    repo_pattern_obj[re.compile("(^ *)image: *" + repo + "/(.*)")] = False

    for line in content:
        bck, newline = process_line(filename, line, repo)
        newcontent.append(newline)
        if needbackup:
            continue
        elif bck:
            needbackup = True

    if needbackup & 0:
        with open(filename + "_bak", "w") as backup:
            backup.writelines(content)

    with open(filename, "w") as newfile:
        newfile.writelines(newcontent)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", type=str, dest="file")
    parser.add_argument("-r", "--repo", type=str, default="{{ localrepo }}", dest="repo")

    args = parser.parse_args()

    for p in repo_pattern:
        repo_pattern_obj[p] = (re.compile(p), True)

    local_repo_pattern = "(^ *)image: *" + args.repo + "/(.*)"
    repo_pattern.insert(0, local_repo_pattern)
    repo_pattern_obj[local_repo_pattern] = (re.compile(local_repo_pattern), False)
    
    local_repo_pattern = "(^ *)- image: *" + args.repo + "/(.*)"
    repo_pattern.insert(1, local_repo_pattern)
    repo_pattern_obj[local_repo_pattern] = (re.compile(local_repo_pattern), False)

    process_file(args.file, args.repo)


if __name__ == "__main__":
    main()
