import os
import requests
import subprocess

repo_query = '''
query
{
    repository(owner: "32blit", name:"32blit-sdk")
    {
        latestRelease
        {
            tagName
        }
    }

    search(query: "topic:32blit", type: REPOSITORY, first:50)
    {
        nodes
        {
            ...on Repository
            {
                nameWithOwner
                url
                latestRelease
                {
                    tagName
                    tagCommit
                    {
                        oid
                    }
                }

                defaultBranchRef
                {
                    name
                    target
                    {
                        oid
                    }
                }
            }
        }
        pageInfo
        {
            endCursor
            hasNextPage
        }
    }
}'''

def github_api_request(query):
    token = os.environ['GITHUB_TOKEN']
    headers = {'Authorization': f'Bearer {token}'}
    res = requests.post('https://api.github.com/graphql', json={'query': query}, headers=headers)

    if res.status_code != 200:
        return None

    return res.json()

def process_repo(repo_status, repo):
    repo_dir = 'repos/' + repo['nameWithOwner']

    cur_sha = None

    # find current sha
    for sha, dir_name, desc in repo_status:
        if dir_name == repo_dir:
            cur_sha = sha
            break

    if repo['latestRelease']:
        new_sha = repo['latestRelease']['tagCommit']['oid']
    else:
        new_sha = repo['defaultBranchRef']['target']['oid']

    # up-to-date
    if new_sha == cur_sha:
        return

    # switch to branch
    branch_name = repo['nameWithOwner']
    result = subprocess.run(['git', 'checkout', branch_name])

    # checkout failed, create new
    if result.returncode:
        result = subprocess.run(['git', 'checkout', '-b', branch_name])
    else:
        # check if the branch already has this sha
        if os.path.exists(repo_dir):
            result = subprocess.run(['git', 'submodule', 'status', repo_dir], capture_output=True)

            if result.returncode == 0:
                print(result.stdout.decode()[1:])
                sha = result.stdout.decode()[1:].split()[0]

                print(sha, new_sha)

                if sha == new_sha:
                    subprocess.run(['git', 'checkout', 'main'])
                    return

        subprocess.run(['git', 'reset', '--hard', 'main'])

    if not cur_sha: # new repo
        subprocess.run(['git', 'submodule', 'add', repo['url'], repo_dir])
        message = f'Add new repo {repo["nameWithOwner"]}\n\n{new_sha}'
    else:
        message = f'Update repo {repo["nameWithOwner"]}\n\n{cur_sha} -> {new_sha}'

    # checkout new sha
    subprocess.run(['git', 'checkout', new_sha], cwd=repo_dir)

    # commit and push
    subprocess.run(['git', 'commit', '-a', '-m', message])
    subprocess.run(['git', 'push', '--force', '-u', 'origin', branch_name])

    # pr
    subprocess.run(['gh', 'pr', 'create', '--fill'])

    # return to main
    subprocess.run(['git', 'checkout', 'main'])

# get current submodules/commit
result = subprocess.run(['git', 'submodule', 'status'], capture_output=True)
repo_status = [x.split() for x in result.stdout.decode().split('\n') if x]

# first page and sdk info
data = github_api_request(repo_query);

if not data:
    exit(1)

while True:
    for repo in data['data']['search']['nodes']:
        process_repo(repo_status, repo)

    if not data['data']['search']['pageInfo']['hasNextPage']:
        break

    #hacky pagination
    cursor = data['data']['search']['pageInfo']['endCursor']
    q = repo_query.replace(', first:50', f', first: 50, after: "{cursor}"')
    data = github_api_request(q)


