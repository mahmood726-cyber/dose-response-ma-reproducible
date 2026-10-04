# Install the R packages used as the reference, from a dated Posit Package Manager snapshot so
# that every machine gets the same versions (dosresmeta 2.2.0, rms 8.1-1, mvmeta 1.0.3 and their
# dependencies as of 2026-10-01). Binary packages are used where PPM provides them.
#   Rscript bench/install_r_packages.R
snapshot <- "https://packagemanager.posit.co/cran/2026-10-01"
if (.Platform$OS.type == "unix" && Sys.info()[["sysname"]] == "Linux" && file.exists("/etc/os-release")) {
  os <- readLines("/etc/os-release")
  codename <- sub("^VERSION_CODENAME=", "", grep("^VERSION_CODENAME=", os, value = TRUE))
  if (length(codename) == 1 && nzchar(codename))   # Linux binaries for the same snapshot date
    snapshot <- sprintf("https://packagemanager.posit.co/cran/__linux__/%s/2026-10-01", codename)
}
options(repos = c(CRAN = snapshot), HTTPUserAgent = sprintf("R/%s R (%s)", getRversion(),
        paste(getRversion(), R.version$platform, R.version$arch, R.version$os)))
need <- c("dosresmeta", "rms", "mvmeta")
missing <- need[!vapply(need, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing)) install.packages(missing, Ncpus = max(1L, parallel::detectCores() - 1L))
for (p in need) cat(p, as.character(packageVersion(p)), "\n")
