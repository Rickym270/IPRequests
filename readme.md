# IPRequests

A small CGI-backed web UI that accepts HTTP request parameters from HTML forms, performs IP-based request actions on the server, and returns/logs results. The project uses classic CGI + HTML forms to collect fields in the browser and execute server-side logic from the Create / Edit / View UI directories.

Status: Prototype / WIP

## Quick overview
IPRequests provides a lightweight web frontend (HTML forms) and server-side CGI handlers that:
- take user-supplied input from form fields,
- perform network/request-related actions server-side (e.g., issue HTTP requests, run lookups, or log metadata),
- present results and let users create, edit, and view saved requests or reports.

The repository is organized with three top-level UI handler directories:
- Create/ — UI and CGI for creating new requests or request definitions
- Edit/ — UI and CGI for modifying existing requests or saved entries
- View/ — UI and CGI for viewing results, status, or logs

## Features
- HTML form-driven UI for issuing requests and collecting parameters
- CGI handlers that receive form POST/GET data and perform the server-side operations
- Basic create / edit / view workflow for request records
- Designed to be simple to deploy on any CGI-capable web server

## Requirements
- A web server with CGI support (Apache with mod_cgi/mod_cgid, Nginx + fcgiwrap, lighttpd, or any compatible server)
- A working CGI interpreter for the scripts in the repository (Perl, Python, Bash, PHP, or whatever the repository's scripts use)
- Appropriate file permissions to execute CGI scripts (executable bit set)
- Optional: network access for any external IP lookups or outgoing HTTP requests the scripts perform

## Install / Deploy (example)
1. Clone the repository:
   git clone https://github.com/Rickym270/IPRequests.git
2. Place the repository or its CGI scripts into your web server's CGI-enabled directory (for example, cgi-bin), or configure the webserver to allow executing CGI in the repo path.
3. Ensure CGI scripts are executable:
   chmod +x *.cgi *.pl *.py
4. Configure your web server to allow POST/GET to the relevant directories, and restart the server.
   - Apache example (in a VirtualHost):
     <Directory "/var/www/html/IPRequests">
       Options +ExecCGI
       AddHandler cgi-script .cgi .pl .py
     </Directory>
5. Navigate to the Create/ or View/ pages in your browser to use the UI.

Local development (quick test using Python's built-in server)
- Put the CGI scripts into a directory named `cgi-bin` inside the repo root, or keep as-is and serve with:
  python3 -m http.server --cgi 8000
- Then open http://localhost:8000/Create/ (or the correct path) in your browser.

## Usage
- Fill the HTML form fields on the Create page to define a new request (URL, source IP/interface, headers, method, etc. — field names depend on the repository's forms).
- Submit the form; the corresponding CGI script will parse the fields (from QUERY_STRING or stdin), execute the action, and return a result page.
- Use Edit to change saved requests and View to display results or logs.

Example (conceptual) form snippet:
<form method="post" action="/Create/submit.cgi">
  <input name="url" type="text" />
  <input name="method" value="GET" />
  <input name="source_ip" />
  <button type="submit">Send</button>
</form>

The CGI script receives these fields and should:
- validate and sanitize input,
- perform the network/request action,
- record logs and return an HTML response.

## Security & best practices
- Never trust form input: validate and sanitize all fields on the server side.
- Run the CGI processes with least privilege (a dedicated user) and avoid executing shell commands with unsanitized input to prevent command injection.
- Use HTTPS for the web UI to protect credentials and input in transit.
- If storing request data or logs, ensure proper file permissions and consider encrypted storage for sensitive data.
- Add rate limiting and authentication if the UI will be public-facing.

## File structure (expected / present)
- Create/ — create form pages and handlers
- Edit/ — edit form pages and handlers
- View/ — result / listing pages
- README.md — (this file)
(The project may also include supporting libraries, templates, or configuration files — inspect the repository to see file extensions like .cgi, .pl, .py, .html, .css, or .conf.)

## Development
- Inspect and run the CGI scripts locally using a CGI-capable server.
- Add unit tests where possible (for non-HTTP logic).
- Consider refactoring repeated CGI parsing and templating logic into a small shared library/module to reduce duplication.

## Troubleshooting
- If script returns "500 Internal Server Error": check web server error logs, ensure scripts are executable and have the correct shebang (#!) line.
- If form fields are empty: verify Content-Type header on the form and that the CGI script reads stdin for POST correctly.
- Use developer tools in the browser and server logs to trace requests.

## Contributing
- Open an issue describing improvements or bugs.
- Fork, create a branch, add tests and documentation, and submit a PR.

## License
- No license file detected in the repository listing responses. Add a LICENSE file to clarify reuse terms (MIT, Apache-2.0, etc.) if you intend to share.

## Contact
Developer/Maintainer: @Rickym270 (GitHub)
