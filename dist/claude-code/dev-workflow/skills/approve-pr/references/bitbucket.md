# Bitbucket

```sh
curl -fsS -H "Authorization: Bearer $BITBUCKET_TOKEN" "$api/pullrequests/$pr"
curl -fsS -X POST -H "Authorization: Bearer $BITBUCKET_TOKEN" "$api/pullrequests/$pr/approve"
curl -fsS -X POST -H "Authorization: Bearer $BITBUCKET_TOKEN" "$api/pullrequests/$pr/merge"
```

