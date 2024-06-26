import pulumi
import pulumi_aws as aws

config = pulumi.Config()

instance_type = config.get("instanceType")
vpc_network_cidr = config.get("vpcNetworkCidr")

ami = aws.ec2.get_ami(
    filters=[
        aws.ec2.GetAmiFilterArgs(
            name="name",
            values=["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-arm64-server-*"],
        ),
        aws.ec2.GetAmiFilterArgs(
            name="architecture",
            values=["arm64"],
        ),
    ],
    owners=["099720109477"],  # Canonical
    most_recent=True,
).id

vpc = aws.ec2.Vpc(
    "vpc",
    cidr_block=vpc_network_cidr,
    enable_dns_hostnames=True,
    enable_dns_support=True,
)

gateway = aws.ec2.InternetGateway("gateway", vpc_id=vpc.id)

subnet = aws.ec2.Subnet(
    "subnet", vpc_id=vpc.id, cidr_block="10.0.1.0/24", map_public_ip_on_launch=True
)

route_table = aws.ec2.RouteTable(
    "routeTable",
    vpc_id=vpc.id,
    routes=[
        aws.ec2.RouteTableRouteArgs(
            cidr_block="0.0.0.0/0",
            gateway_id=gateway.id,
        )
    ],
)

route_table_association = aws.ec2.RouteTableAssociation(
    "routeTableAssociation", subnet_id=subnet.id, route_table_id=route_table.id
)

ports = (("tcp", 80), ("tcp", 443), ("tcp", 22), ("tcp", 6443))
ingress = [
    aws.ec2.SecurityGroupIngressArgs(
        from_port=port, to_port=port, protocol=protocol, cidr_blocks=["0.0.0.0/0"]
    )
    for protocol, port in ports
]

sec_group = aws.ec2.SecurityGroup(
    "secGroup",
    description="Enable HTTP access",
    vpc_id=vpc.id,
    ingress=ingress,
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            from_port=0,
            to_port=0,
            protocol="-1",
            cidr_blocks=["0.0.0.0/0"],
        )
    ],
)

existing_key_pair = aws.ec2.KeyPair.get("existingKeyPair", "aws")

server = aws.ec2.Instance(
    "spark-server",
    instance_type=instance_type,
    subnet_id=subnet.id,
    vpc_security_group_ids=[sec_group.id],
    ami=ami,
    key_name=existing_key_pair.key_name,
    root_block_device=aws.ec2.InstanceRootBlockDeviceArgs(
        volume_size=15, volume_type="gp3"
    ),
    tags={
        "Name": "spark",
    },
)

pulumi.export("Server IP", server.public_ip)
pulumi.export("Server hostname", server.public_dns)
pulumi.export(
    "Server url", server.public_dns.apply(lambda public_dns: f"http://{public_dns}")
)

num_agents = 2
for i in range(num_agents):
    agent = aws.ec2.Instance(
        f"spark-agent-{i}",
        instance_type=instance_type,
        subnet_id=subnet.id,
        vpc_security_group_ids=[sec_group.id],
        ami=ami,
        key_name=existing_key_pair.key_name,
        root_block_device=aws.ec2.InstanceRootBlockDeviceArgs(
            volume_size=15, volume_type="gp3"
        ),
        tags={
            "Name": "spark",
        },
    )

    pulumi.export(f"Agent {i} IP", agent.public_ip)
    pulumi.export(f"Agent {i} hostname", agent.public_dns)
    pulumi.export(
        f"Agent {i} url",
        agent.public_dns.apply(lambda public_dns: f"http://{public_dns}"),
    )
