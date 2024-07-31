# see: https://developers.google.com/idx/guides/customize-idx-env
{ pkgs, ... }: {
    # Which nixpkgs channel to use.
    channel = "stable-23.11"; # or "unstable"
    
    # List packages you want available in your environment
    packages = [ 
        pkgs.python311
        pkgs.python311Packages.pip
        pkgs.python311Packages.virtualenv
    ]; 
    idx = {
        workspace = {
            onCreate = {
                python-vent-install = "python -m venv .env";
            };
            onStart = {
                # python-start = "python -m venv .env";
            };
        };
    };
}
