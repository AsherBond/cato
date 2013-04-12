def check_license(app=""):
    # this is important... if anything fails on the license check...
    # we ALLOW access.  Don't want any bugs to limit the ability to use the software.
    filename = "../../LICENSE"
    with open(filename, 'r') as f_in:
        license_text = f_in.read()

    # check the encoding to see if it's ascii, if not, use the default message
    try:
        license_text.encode("ascii")
    except:
        license_text = None

    if not license_text:
        license_text = """Copyright 2012 Cloud Sidekick

                Use of this software indicates agreement with the included software LICENSE.

                The LICENSE can be found in the application directory where this Cloud Sidekick product is installed.
                """
        
    # the value will either be 'agreed' or ''
    from catosettings import settings
    license_status = settings.settings.get_application_setting("general/%slicense_status" % ("%s_" % app if app else ""))
    
    # the value will either be 'agreed' or ''
    if license_status == "agreed":
        return "pass", "", ""
    else:
        # not agreed, return the LICENSE file.
        return "fail", "", license_text
