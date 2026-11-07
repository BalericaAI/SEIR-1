#!/bin/bash

# install web server
apt update -y

# moved php install to before file creation
apt install -y apache2 php libapache2-mod-php

# remove default apache page
rm -f /var/www/html/index.html

# create our own web page
cat <<'EOF' > /var/www/html/index.php
<?php
$banners = [
"SEIR_NODE" => "
      ███████╗███████╗██╗██████╗
      ██╔════╝██╔════╝██║██╔══██╗
      ███████╗█████╗  ██║██████╔╝
      ╚════██║██╔══╝  ██║██╔══██╗
      ███████║███████╗██║██║  ██║
      ╚══════╝╚══════╝╚═╝╚═╝  ╚═╝
",
"VADER" => "
        ⠀⠀⠀⠀⠀⢀█████⡀
     ⠀⠀⠀⠀⢠███⣿⣿⣿███⡄
    ⠀⠀⠀⢀██⣿⣿⣿⣿⣿⣿⣿██⡀
   ⠀⠀⠀⣾⣿⣿⣿⡿⠿⠿⠿⡿⣿⣿⣷
   ⠀⠀⠀⣿⣿⣿⠃⠀⠀⠀⠀⠘⣿⣿⣿
   ⠀⠀⠀⣿⣿⣿⠀⣀⠀⠀⣀⠀⣿⣿⣿
   ⠀⠀⠀⣿⣿⣿⣧⣿⣧⣰⣿⠀⣼⣿⣿
   ⠀⠀⠀⠘⣿⣿⣿⣦⣀⣉⣉⣴⣿⣿⠃
      ⠀⠀⠀⠈⠻████████⠟⠁
",
"STATE_WARNING" => "
████████████████████████████████
WARNING: TERRAFORM STATE FILE LOST
ENGINEERS ENTERING PRAYER MODE
████████████████████████████████
",
"STATUS" => "
SEIR NODE STATUS
Terraform State : SAFE
Graph API       : ANGRY
Students        : CONFUSED
Instructor      : PLEASED
",
"FRIDAY13" => "
FRIDAY THE 13TH NODE
Infrastructure Online
Dark Side Active
Proceed With Terraform
"
];
$banner = $banners[array_rand($banners)];
?>
<html>
<head>
<title>SEIR Infrastructure Node</title>
<style>
body {
background:black;
color:lime;
font-family:monospace;
text-align:center;
}
pre {
font-size:16px;
}
</style>
</head>
<body>
<h1>SEIR Infrastructure Node Online</h1>
<pre>
<?php echo $banner; ?>
</pre>
<p>Refresh the page to observe infrastructure randomness.</p>
</body>
</html>
EOF

# enable apache
systemctl restart apache2
systemctl enable apache2
