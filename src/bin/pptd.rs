use clap::Parser;
use open_pptd::cli::Cli;

fn main() {
    std::process::exit(Cli::parse().run());
}
