# Azure DevOps

```sh
az repos pr show --id "$pr" --query '{id:pullRequestId,status:status,isDraft:isDraft,target:targetRefName,mergeStatus:mergeStatus}'
az repos pr policy list --id "$pr" && az repos pr set-vote --id "$pr" --vote approve
az repos pr update --id "$pr" --status completed --bypass-policy false
```

