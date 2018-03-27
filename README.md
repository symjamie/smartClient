# smartClient
Author:  Yiming Sun
Date:  Jan 26, 2018

------------------------------------------------
Execution environment:
	Python 3.6

------------------------------------------------
Input:
	A valid hostname in argument line. (e.g. run the program with "$python3 SmartClient.py uvic.ca").
	The third-level domain (e.g. "www") is optional.

------------------------------------------------
Output:
	The hostname from the argument line, and:
	1. Whether the host supports HTTPS ("yes" or "no"; "no" if an error occur).
	2. The newest HTTP version that the host uses ("HTTP/1.0", "HTTP/1.1" or "HTTP/2.0"; "N/A" if an error occur).
	3. A list of Cookies in all the response headers (e.g. in both "302" responses and redirected "200" responses;
	   "none" if no Cookies found, or an error occur; dynamic Cookies are not presented).

------------------------------------------------
Error handlings:
	1. Notify the user if number of arguments is not 2.
	2. Notify the user if the hostname contains a protocol name (e.g. "https://") or is invalid (e.g. "uvic..ca").
	3. Output an error if socket can not be created.
	4. Output an error if the socket can not connect to the host (i.e. the host does not exist, e.g. "uvic.c").
	5. Throw an exception in function negotiate_tls() if TLS connection can not be created.
