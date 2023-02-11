import json
import os
import shutil
import git

if __name__ == '__main__':
    gist_id = os.environ['INPUT_GIST_ID']
    path = os.environ['INPUT_SOURCE_PATH']
    token = os.environ['INPUT_GIST_TOKEN']

    print(json.dumps(os.environ, indent=4))
    exit(0)

    # checking source
    if not os.path.isdir(path):
        raise ValueError(f'Invalid source path. {path} is not directory.')

    # list files on source
    source_list = os.listdir(path)
    source_files = []
    source_skipped = {
        'is_directory': [],
        'non_text_or_unreadable': [],
    }

    for file in source_list:
        if os.path.isdir(os.path.join(path, file)):
            source_skipped['is_directory'].append(file)
            continue
        source_files.append(file)

    source_files_content = {}
    # prepare files content
    for file in source_files:
        try:
            # with utf-8, to avoid binary files
            with open(os.path.join(path, file), 'r', encoding='utf-8') as f:
                content = f.read()
                source_files_content[file] = content
        # all exception
        except Exception:
            source_skipped['non_text_or_unreadable'].append(file)
            source_files.remove(file)

    print(f'Skipped files from source: {source_skipped}')
    print(f'Found {len(source_files)} readable files from source: {source_files}')

    # define gist git
    gist_git_url = f'https://{token}@gist.github.com/{gist_id}.git'
    gist_git_dir = f'gist-clones/{gist_id}'

    # reset working directory
    if os.path.isdir(gist_git_dir):
        shutil.rmtree(gist_git_dir)
    elif os.path.isfile(gist_git_dir):
        os.remove(gist_git_dir)

    try:

        # start cloning gist
        # can't use API, as API only limit to 300 files in list, and more importantly can't add new file
        # https://docs.github.com/en/rest/gists/gists?apiVersion=2022-11-28#about-gists
        git.Repo.clone_from(gist_git_url, gist_git_dir, depth=1)

        target_files = os.listdir(gist_git_dir)
        # since its git, skip .git dit
        if '.git' in target_files:
            target_files.remove('.git')

        print(f'Found {len(target_files)} files in gist')

        # file to remove
        removed_files = []
        for file in target_files:
            if file not in source_files:
                os.remove(os.path.join(gist_git_dir, file))
                removed_files.append(file)

        print(f'Removed {len(removed_files)} files from Gist repo: {removed_files}')

        # update or add
        for file in source_files:
            # basically copy replace
            if os.path.isfile(os.path.join(gist_git_dir, file)):
                os.remove(os.path.join(gist_git_dir, file))
            shutil.copy(os.path.join(path, file), os.path.join(gist_git_dir, file), follow_symlinks=False)

        gist_repo = git.Repo(gist_git_dir)

        with gist_repo.config_writer() as git_config:
            git_config.set_value('user', 'email', os.environ['GITHUB_ACTOR'])
            git_config.set_value('user', 'name', f'{os.environ["GITHUB_ACTOR"]}@users.noreply.github.com')

        # no changes detected, get out with "success-ish"
        if not gist_repo.is_dirty():
            print(f'No changes detected in Gist repo.')
            exit(0)

        if len(removed_files):
            gist_repo.index.remove(removed_files)

        if len(source_files):
            gist_repo.index.add(source_files)

        gist_repo.index.commit('Sync from repo.')
        gist_repo.remotes.origin.push()

        print(f'Pushed changes to Gist repo.')
    except Exception:
        raise ValueError('Unable to work with gist git')
