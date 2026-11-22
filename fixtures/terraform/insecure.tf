resource "aws_s3_bucket" "public_data" {
  acl = "public-read"
}

resource "aws_security_group" "open_ssh" {
  ingress {
    cidr_blocks = ["0.0.0.0/0"]
  }
}
