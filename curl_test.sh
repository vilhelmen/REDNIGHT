auth_key=$(curl -X GET 192.168.52.131/users/sign_in -c session_cookie | grep -o -E 'name="authenticity_token".*value="[^"]*"' | cut -d \" -f4)
