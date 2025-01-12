# deploy.tf

# Provider Configuration
provider "aws" {
  region = var.aws_region
}

# Variables
variable "aws_region" {
  description = "The AWS region to deploy resources in."
  default     = "us-east-1"
}

variable "instance_type" {
  description = "EC2 instance type."
  default     = "t3.large"
}

variable "ami_id" {
  description = "AMI ID for the EC2 instance."
  default     = "ami-0e2c8caa4b6378d8c" # Ubuntu, SSD Volume Type for us-east-1
}

variable "key_name" {
  description = "Name of the SSH key pair."
  type        = string
  default     = "chatbot"
}

variable "allowed_ip" {
  description = "Your IP address with CIDR notation for SSH access."
  type        = string
  default     = "108.28.107.19/32"
}

variable "OPENAI_API_KEY" {
  description = "API Key"
  type        = string
  sensitive   = true
}

variable "LANGSMITH_API_KEY" {
  description = "API Key"
  type        = string
  sensitive   = true
}

variable "TAVILY_API_KEY" {
  description = "API Key"
  type        = string
  sensitive   = true
}

resource "aws_key_pair" "chatbot" {
  key_name   = "chatbot"
  public_key = file("/Users/kevinhsu/Downloads/chatbot.pub")
}

# Security Group
resource "aws_security_group" "gmuchatbot_sg" {
  name        = "gmuchatbot_sg"
  description = "Security group for GMU Chatbot EC2 instance"

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.allowed_ip]
  }

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Gradio"
    from_port   = 8501
    to_port     = 8501
    protocol    = "tcp"
    cidr_blocks = [var.allowed_ip]
  }

  # Egress Rules
  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"                 # All protocols
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "gmuchatbot_sg"
  }
}

# EC2 Instance
resource "aws_instance" "gmuchatbot_ec2" {
  ami                         = var.ami_id
  instance_type               = var.instance_type
  key_name                    = var.key_name
  vpc_security_group_ids      = [aws_security_group.gmuchatbot_sg.id]
  associate_public_ip_address = true

  # Root Block Device Configuration
  root_block_device {
    volume_size           = 30               # Size in GiBs
    volume_type           = "gp3"            # Volume type (gp3 is recommended for general-purpose SSD)
    delete_on_termination = true             # Deletes the volume when the instance is terminated
    encrypted             = true             # Encrypt the volume for data security
  }


user_data = <<-EOF
  #!/bin/bash
  sudo apt-get update -y
  sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common git unzip
  # Install Docker
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
  sudo add-apt-repository \
     "deb [arch=$(dpkg --print-architecture)] https://download.docker.com/linux/ubuntu \
     $(lsb_release -cs) \
     stable"
  sudo apt-get update -y
  sudo apt-get install -y docker-ce docker-ce-cli containerd.io

  # Install Docker Compose V2 as a Docker CLI plugin
  sudo mkdir -p /usr/lib/docker/cli-plugins/
  # Install Docker Compose
  sudo curl -SL "https://github.com/docker/compose/releases/download/v2.20.2/docker-compose-linux-x86_64" \
  -o /usr/lib/docker/cli-plugins/docker-compose
  sudo chmod +x /usr/lib/docker/cli-plugins/docker-compose
  sudo usermod -aG docker ubuntu
  # Optional: Clone your repository and run Docker containers
  sudo apt-get install -y git
  git clone https://github.com/kevin000001505/GMU-chatbot.git /home/ubuntu/GMU-chatbot
  cd /home/ubuntu/GMU-chatbot
  # Create .env file with interpolated variables
  cat <<EOT >> .env
  OPENAI_API_KEY=${var.OPENAI_API_KEY}
  LANGSMITH_API_KEY=${var.LANGSMITH_API_KEY}
  TAVILY_API_KEY=${var.TAVILY_API_KEY}
  EOT
  chmod 600 .env
  sudo chown ubuntu:ubuntu .env
  sudo systemctl enable docker
  cd /home/ubuntu/GMU-chatbot
  sudo docker compose up -d --build --force-recreate
EOF

  tags = {
    Name = "GMU-Chatbot-Instance"
  }
}

# Outputs
output "instance_public_ip" {
  description = "The public IP address of the EC2 instance."
  value       = aws_instance.gmuchatbot_ec2.public_ip
}

output "instance_public_dns" {
  description = "The public DNS of the EC2 instance."
  value       = aws_instance.gmuchatbot_ec2.public_dns
}