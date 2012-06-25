def check_license():
    # this is important... if anything fails on the license check...
    # we ALLOW access.  Don't want any bugs to limit the ability to use the software.
    try:
        filename = "../LICENSE"
        with open(filename, 'r') as f_in:
            license_text = f_in.read()

        if not license_text:
            license_text = """<p>
                    Copyright 2012 Cloud Sidekick
                </p>
                <p>
                    Use of this software indicates agreement with the included software LICENSE.
                </p>
                <p>
                    The LICENSE can be found in the application directory where this Cloud Sidekick product is installed.
                </p>"""
            
        # the value will either be 'agreed' or ''
        from settings import settings
        license_status = settings.settings.get_application_setting("general/license_status")
        
        # the value will either be 'agreed' or ''
        if license_status == "agreed":
            return "pass", "", ""
        else:
            # not agreed, return the LICENSE file.
            return "fail", "", license_text

    except Exception as ex:
        print(ex.__str__())    
