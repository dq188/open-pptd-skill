use clap::Parser;
use open_pptd::cli::Cli;

fn main() {
    #[cfg(unix)]
    unsafe {
        unsafe extern "C" {
            fn signal(sig: i32, handler: usize) -> usize;
        }
        signal(13, 0); // SIGPIPE = 13, SIG_DFL = 0
    }

    std::process::exit(Cli::parse().run());
}
