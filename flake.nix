{
  description = "NetOrbit - terminal-native outbound IPv4 traffic visualizer";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" ];
      forAllSystems = f:
        nixpkgs.lib.genAttrs systems (system:
          f (import nixpkgs { inherit system; }));
    in
    {
      packages = forAllSystems (pkgs:
        let
          python = pkgs.python314;
        in
        {
          default = python.pkgs.buildPythonApplication {
            pname = "netorbit";
            version = "0.1.0";
            src = self;

            pyproject = true;

            nativeBuildInputs = with python.pkgs; [
              setuptools
              wheel
            ];

            propagatedBuildInputs = with python.pkgs; [
              rich
              textual
              scapy
              requests
            ];

            meta = {
              description = "Terminal-native outbound IPv4 traffic visualizer";
              mainProgram = "netorbit";
            };
          };
        });

      apps = forAllSystems (pkgs: {
        default = {
          type = "app";
          program = "${self.packages.${pkgs.stdenv.hostPlatform.system}.default}/bin/netorbit";
        };
      });

      devShells = forAllSystems (pkgs: {
        default = pkgs.mkShell {
          packages = [
            pkgs.python314
            pkgs.python314Packages.pip
            pkgs.python314Packages.rich
            pkgs.python314Packages.textual
            pkgs.python314Packages.scapy
            pkgs.python314Packages.requests
          ];
        };
      });
    };
}
