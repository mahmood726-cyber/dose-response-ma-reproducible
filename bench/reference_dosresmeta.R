# Reference fits from dosresmeta for every dataset in the corpus.
# Studies with a missing case or total count are excluded (the Greenland-Longnecker
# covariance needs both); datasets left with fewer than 2 studies are skipped.
#
#   linear : dosresmeta(logrr ~ dose, id, type, se, cases, n, method = "reml")      (covariance "gl")
#   spline3: dosresmeta(logrr ~ rcs(dose, k3), ...), k3 = quantile(dose, c(.10, .50, .90))
#   spline4: dosresmeta(logrr ~ rcs(dose, k4), ...), k4 = quantile(dose, c(.05, .35, .65, .95))
#   fitted log-RR (spline3) on a grid of 9 doses from 0 to the 95th percentile, versus dose 0,
#   for datasets whose smallest dose is 0.
# Output: one JSON object per line, numbers written with 17 significant digits.
#
#   Rscript bench/reference_dosresmeta.R data/corpus.csv results/dosresmeta.jsonl
suppressMessages({ library(dosresmeta); library(rms) })
args <- commandArgs(trailingOnly = TRUE)
corpus <- read.csv(args[1], stringsAsFactors = FALSE)
out <- args[2]
num <- function(x) ifelse(is.finite(x), formatC(x, digits = 17, format = "g"), "null")
vec <- function(x) paste0("[", paste(num(as.numeric(x)), collapse = ","), "]")
err <- function(e) sprintf('{"ok":false,"error":"%s"}', gsub('["\\\\\n\r]', " ", substr(as.character(e), 1, 140)))
splfit <- function(d, probs) {
  k <- quantile(d$dose, probs)
  f <- try(dosresmeta(formula = logrr ~ rcs(dose, k), id = id, type = type, se = se, cases = cases, n = n,
                      data = d, method = "reml"), silent = TRUE)
  list(k = k, f = f)
}
lines <- character()
for (ds in unique(corpus$dataset)) {
  d <- corpus[corpus$dataset == ds, ]
  bad <- unique(d$id[is.na(d$cases) | is.na(d$n)])
  d <- d[!d$id %in% bad, ]
  ids <- unique(d$id)
  head <- sprintf('"dataset":"%s","k":%d,"excluded_studies":%d', ds, length(ids), length(bad))
  if (length(ids) < 2) {
    msg <- '{"ok":false,"error":"fewer than 2 studies with counts"}'
    lines <- c(lines, sprintf('{%s,"linear":%s,"spline3":%s,"spline4":%s}', head, msg, msg, msg)); next
  }
  d$id <- factor(d$id, levels = ids)
  lin <- try(dosresmeta(formula = logrr ~ dose, id = id, type = type, se = se, cases = cases, n = n,
                        data = d, method = "reml"), silent = TRUE)
  linj <- if (inherits(lin, "try-error")) err(lin) else
    sprintf('{"ok":true,"b":%s,"se":%s,"tau2":%s}', num(coef(lin)[1]), num(sqrt(vcov(lin)[1, 1])), num(as.numeric(lin$Psi)[1]))
  sj <- list()
  for (nk in c(3, 4)) {
    s <- splfit(d, if (nk == 3) c(.10, .50, .90) else c(.05, .35, .65, .95))
    sj[[nk]] <- if (inherits(s$f, "try-error")) err(s$f) else {
      pred <- "null"; grid <- "null"
      if (nk == 3 && min(d$dose) == 0) {
        g <- seq(0, as.numeric(quantile(d$dose, .95)), length.out = 9)
        p <- predict(s$f, data.frame(dose = g), xref = 0, expo = FALSE)
        grid <- vec(g); pred <- vec(p$pred)
        predse <- vec((p$ci.ub - p$pred) / qnorm(0.975))
      } else predse <- "null"
      sprintf('{"ok":true,"knots":%s,"beta":%s,"cov":%s,"Psi":%s,"grid":%s,"pred":%s,"pred_se":%s}',
              vec(s$k), vec(coef(s$f)), vec(vcov(s$f)), vec(s$f$Psi), grid, pred, predse)
    }
  }
  lines <- c(lines, sprintf('{%s,"linear":%s,"spline3":%s,"spline4":%s}', head, linj, sj[[3]], sj[[4]]))
  cat(".")
}
dir.create(dirname(out), showWarnings = FALSE, recursive = TRUE)
writeLines(lines, out, useBytes = TRUE)
cat(sprintf("\ndosresmeta %s, rms %s, mvmeta %s, R %s -> %s\n", packageVersion("dosresmeta"), packageVersion("rms"),
            packageVersion("mvmeta"), getRversion(), out))
