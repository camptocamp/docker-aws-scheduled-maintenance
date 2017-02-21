# Prometheus gateway for AWS notifications

This container launch a Prometheus collector registry and pushes
notifications to a Prometheus push gateway.

It intends to be launched on a regular basis, and wants a host named
pushgateway.metrics listening on port 9091.

## Usage
### Environment variables
* AWS_ACCESS_KEY_ID - AWS Access key ID for the API calls
* AWS_SECRET_ACCESS_KEY - AWS Secret key for the API calls
* AWS_REGION_NAME - the AWS region name (eu-west-1, us-east-1, and so on)

### IAM rights
The user should be able to have at least *read* access to ec2 subset. A typical rule:
```JSON
{
  "Version": "2012-10-17",
  "Statement": {
    "Effect": "Allow",
    "Action": [
      "ec2:List*",
      "ec2:Get*"
    ],
    "Resource": "*"
  }
}
```
Of course, we strongly advice you create a dedicate user for this container.

## TODO
- implement a better support for instance roles and profiles (in order to drop the need of env var)
- send other information to prometheus (like RDS maintenance announcements)
