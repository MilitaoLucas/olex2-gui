# Convert svn to git 
Use the following [link](https://stackoverflow.com/questions/79165/how-do-i-migrate-an-svn-repository-with-history-to-a-new-git-repository#3972103) to the original post

Create a users file (i.e. `users.txt`) for mapping SVN users to Git:
```
user1 = First Last Name <email@address.com>
user2 = First Last Name <email@address.com>
...
```
You can use this one-liner to build a template from your existing SVN repository:
```
svn log -q | awk -F '|' '/^r/ {gsub(/ /, "", $2); sub(" $", "", $2); print $2" = "$2" <"$2">"}' | sort -u > users.txt
```
SVN will stop if it finds a missing SVN user, not in the file. But after that, you can update the file and pick up where you left off.

Now pull the SVN data from the repository:
```
git svn clone --stdlayout --no-metadata --authors-file=users.txt svn://hostname/path dest_dir-tmp
```
When completed, Git will checkout the SVN `trunk` into a new branch. Any other branches are set up as remotes. You can view the other SVN branches with:
```
git branch -r
```
If you want to keep other remote branches in your repository, you want to create a local branch for each one manually. (Skip trunk/master.) If you don't do this, the branches won't get cloned in the final step.
```
git checkout -b local_branch remote_branch
# It's OK if local_branch and remote_branch are the same names
```
Tags are imported as branches. You have to create a local branch, make a tag and delete the branch to have them as tags in Git. To do it with tag "v1":
```
git checkout -b tag_v1 remotes/tags/v1
git checkout master
git tag v1 tag_v1
git branch -D tag_v1
```
Clone your GIT-SVN repository into a clean Git repository:
```
git clone dest_dir-tmp dest_dir
rm -rf dest_dir-tmp
cd dest_dir
```
The local branches that you created earlier from remote branches will only have been copied as remote branches into the newly cloned repository. (Skip trunk/master.) For each branch you want to keep:
```
git checkout -b local_branch origin/remote_branch
```
Finally, remove the remote from your clean Git repository that points to the now-deleted temporary repository:
```
git remote rm origin
```
