# Usage: Rscript bench/build_corpus.R data/corpus.csv
# Dose-response validation corpus: every multi-study binary (log RR / log OR) dataset shipped
# with the R package dosresmeta, in one standard long format:
#   dataset, id, type (cc / ci / ir), dose, cases, n (persons, or person-time for "ir"), logrr, se
# Reference rows have se = NA. Excluded: ari (continuous outcome, not supported by the app)
# and cc_ex / ci_ex / ir_ex (single-study examples).
suppressMessages(library(dosresmeta))
args <- commandArgs(trailingOnly = TRUE)
out <- if (length(args)) args[1] else "data/corpus.csv"
get_ds <- function(d) { e <- new.env(); data(list = d, package = "dosresmeta", envir = e); get(d, envir = e) }
spec <- list(
  alcohol_crc = c(dose = "dose", cases = "cases", n = "peryears", logrr = "logrr", se = "se"),
  alcohol_cvd = c(dose = "dose", cases = "cases", n = "n", logrr = "logrr", se = "se"),
  alcohol_esoph = c(dose = "dose", cases = "cases", n = "n", logrr = "logrr", se = "se"),
  alcohol_lc = c(dose = "dose", cases = "cases", n = "peryears", logrr = "logrr", se = "se"),
  bmi_rc = c(dose = "bmi", cases = "case", n = "n", logrr = "logor", se = "se_logor"),
  coffee_cancer = c(dose = "dose", cases = "cases", n = "n", logrr = "logrr", se = "se"),
  coffee_cvd = c(dose = "dose", cases = "cases", n = "n", logrr = "logrr", se = "se"),
  coffee_mort = c(dose = "dose", cases = "cases", n = "n", logrr = "logrr", se = "se"),
  coffee_mort_add = c(dose = "dose", cases = "cases", n = "n", logrr = "logrr", se = "se"),
  coffee_stroke = c(dose = "dose", cases = "cases", n = "n", logrr = "logrr", se = "se"),
  fish_ra = c(dose = "dose", cases = "cases", n = "n", logrr = "logrr", se = "se"),
  milk_mort = c(dose = "dose", cases = "cases", n = "n", logrr = "logrr", se = "se"),
  milk_ov = c(dose = "dose", cases = "case", n = "n", logrr = "logrr", se = "se"),
  oc_breast = c(dose = "duration", cases = "cases", n = "n", logrr = "logor", se = "se"),
  process_bc = c(dose = "dose", cases = "cases", n = "n", logrr = "logrr", se = "se"),
  red_bc = c(dose = "dose", cases = "cases", n = "n", logrr = "logrr", se = "se"),
  sim_os = c(dose = "dose", cases = "cases", n = "n", logrr = "logrr", se = "se")
)
L <- list()
for (d in names(spec)) {
  x <- get_ds(d); m <- spec[[d]]
  L[[d]] <- data.frame(dataset = d, id = as.character(x$id), type = as.character(x$type),
                       dose = x[[m["dose"]]], cases = x[[m["cases"]]], n = x[[m["n"]]],
                       logrr = x[[m["logrr"]]], se = x[[m["se"]]], stringsAsFactors = FALSE)
}
corpus <- do.call(rbind, L)
dir.create(dirname(out), showWarnings = FALSE, recursive = TRUE)
write.csv(corpus, out, row.names = FALSE, fileEncoding = "UTF-8")
cat(sprintf("corpus: %d datasets, %d studies, %d rows (dosresmeta %s)\n", length(spec),
            nrow(unique(corpus[, c("dataset", "id")])), nrow(corpus), packageVersion("dosresmeta")))
print(table(corpus$dataset, corpus$type))
