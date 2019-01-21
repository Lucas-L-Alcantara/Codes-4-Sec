
# Requirements: awscli, python3, boto3
# by github.com/Lucas-L-Alcantara
#.
#..
#...
# Script for list aws ec2 instances with public port

import boto3
import json
from collections import defaultdict
from prettytable import PrettyTable
from botocore.exceptions import ClientError
import argparse

x = PrettyTable()
x.field_names = ["Name", "ID", "SGs", "Private IP", "Public IP", "Public Ports", "Region"]


parser = argparse.ArgumentParser()
parser.add_argument("-p", "--profile", help="Example: get_public_ports.py -p <aws_profile_name>")
args = parser.parse_args()
global iamuser
pname = args.profile

if pname is not None:

	boto3.setup_default_session(profile_name=pname, region_name="us-east-1")


client = boto3.client('ec2')

ec2info = defaultdict()

acc_name =   str(boto3.client('iam').list_account_aliases()['AccountAliases'][0])

regions = [region['RegionName'] for region in client.describe_regions()['Regions']]



for region in regions:

	print("\nSearching in: ", region)
	
	ec2r= boto3.resource('ec2', region_name=region)

	running_instances = ec2r.instances.filter(Filters=[{
	    'Name': 'instance-state-name',
	    'Values': ['running']}])


	for instance in running_instances:
		
		name = "Null"
		if instance.tags is not None:
			for tag in instance.tags:
				if tag['Key'] == 'Name':			
					name = tag['Value']

			
		if instance.public_ip_address is not None:
			
			sgs=[]
			
			for i in range(len(instance.security_groups)):
				
				sg_id=instance.security_groups[i]['GroupId']
				sgs.append(sg_id)
			
				open_ports = []	
			
			sg = ec2r.SecurityGroup(sg_id)

			try:
				
				for i in range(len(sg.ip_permissions)):
					to_port = ''
					ip_proto = ''
					if 'ToPort' in sg.ip_permissions[i]:
						to_port = sg.ip_permissions[i]['ToPort']
					if 'IpProtocol' in sg.ip_permissions[i]:
						ip_proto = sg.ip_permissions[i]['IpProtocol']
						if '-1' in ip_proto:
							ip_proto = 'All'
					for j in range(len(sg.ip_permissions[i]['IpRanges'])):
						cidr_ports = "%s" % (to_port)
			
						if sg.ip_permissions[i]['IpRanges'][j]['CidrIp'] == '0.0.0.0/0':

							if ip_proto != 'icmp':
								open_ports.append(cidr_ports)

			except ClientError as e:
			    if e.response['Error']['Code'] == 'InvalidGroup.NotFound':
			        print("ERROR - SG does not exist.")
			    else:
			        print("Unexpected error: %s" % e)

		 
			if len(sgs):
				sgl = (', '.join(str(s) for s in sgs))
			
				if len(open_ports):
						ports = (', '.join(str(p) for p in open_ports))
						x.add_row([name, instance.id, sgl, instance.private_ip_address ,instance.public_ip_address, ports, region])
	        
print("\n------------------------------------------------")
print(" Public EC2 Ports from ", acc_name," Account:")
print("------------------------------------------------\n")

print(x, "\n")
