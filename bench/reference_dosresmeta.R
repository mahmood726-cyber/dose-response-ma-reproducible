# Reference fits from dosresmeta for every dataset in the corpus, across the grid of models
# and options the app supports. Studies with a missing case or total count are excluded (the
# Greenland-Longnecker and Hamling covariances need both); datasets left with fewer than 2
# studies are skipped.
#
#   models      linear (logrr ~ dose), quadratic (+ I(dose^2)), rcs3/rcs4/rcs5
#               (rms::rcs, knots = quantile(dose, Harrell's percentiles))
#   grid        GL covariance: every model x {2stage reml/ml/fixed/mm, 1stage reml/ml/fixed};
#               Hamling: linear/rcs3/rcs4 x {2stage, 1stage} reml; independent: linear/rcs3 x
#               {2stage, 1stage} reml; meta-regression (2stage reml, linear and rcs3):
#               coffee_mort ~ year, coffee_stroke ~ nordic
#   per fit     coefficients, vcov, Psi, logLik, convergence, qtest, Wald tests, gof(), and
#               predictions on 7 doses (min, 10/25/50/75/90th percentiles, max) versus the min
#   refusals    recorded with dosresmeta's error message
# Output: one JSON object per dataset per line, numbers with 17 significant digits.
#
#   Rscript bench/reference_dosresmeta.R results/full/corpus.csv results/full/dosresmeta.jsonl
suppressMessages({ library(dosresmeta); library(rms) })
args <- commandArgs(trailingOnly = TRUE)
corpus <- read.csv(args[1], stringsAsFactors = FALSE)
out <- args[2]
get_ds <- function(d) { e <- new.env(); data(list = d, package = "dosresmeta", envir = e); get(d, envir = e) }
MOD <- c(coffee_mort = "year", coffee_stroke = "nordic")   # study-level covariates used for meta-regression
PROBS <- list(rcs3 = c(.10, .50, .90), rcs4 = c(.05, .35, .65, .95), rcs5 = c(.05, .275, .50, .725, .95))

num <- function(x) ifelse(is.finite(x), formatC(x, digits = 17, format = "g"), "null")
vec <- function(x) paste0("[", paste(num(as.numeric(x)), collapse = ","), "]")
str <- function(s) paste0('"', gsub('["\\\\\n\r\t]', " ", s), '"')
obj <- function(...) { a <- list(...); a <- a[!vapply(a, is.null, NA)]; paste0("{", paste(paste0('"', names(a), '":', unlist(a)), collapse = ","), "}") }

fitone <- function(d, model, covariance, proc, method, mod = NULL) {
  k <- if (startsWith(model, "rcs")) as.numeric(quantile(d$dose, PROBS[[model]])) else NULL
  fml <- switch(model, linear = logrr ~ dose, quadratic = logrr ~ dose + I(dose^2), logrr ~ rcs(dose, k))
  environment(fml) <- environment()
  a <- list(formula = fml, id = d$id, type = d$type, se = d$se, cases = d$cases, n = d$n, data = d,
            covariance = covariance, proc = proc, method = method)
  if (!is.null(mod)) a$mod <- as.formula(paste("~", mod))
  f <- try(suppressWarnings(do.call(dosresmeta, a)), silent = TRUE)
  head <- list(model = str(model), covariance = str(covariance), proc = str(proc), method = str(method),
               mod = if (is.null(mod)) NULL else str(mod), knots = if (is.null(k)) NULL else vec(k))
  if (inherits(f, "try-error")) return(do.call(obj, c(head, list(ok = "false", error = str(substr(as.character(f), 1, 200))))))
  b <- coef(f); V <- vcov(f); q <- f$dim$q
  wall <- waldtest(Sigma = V, b = b, Terms = seq_along(b))$chitest
  wnl <- if (q > 1 && is.null(mod)) waldtest(Sigma = V, b = b, Terms = 2:q)$chitest else NULL
  qt <- if (proc == "2stage") qtest(f) else NULL
  g <- try(gof(f), silent = TRUE)
  gj <- if (inherits(g, "try-error")) NULL else
    obj(D = num(g$deviance$D), df = num(g$deviance$df), p = num(g$deviance$p), R2 = num(g$R2), R2adj = num(g$R2adj), resid = vec(g$tdata$tresiduals))
  pj <- NULL
  if (is.null(mod)) {
    grid <- c(min(d$dose), as.numeric(quantile(d$dose, c(.1, .25, .5, .75, .9))), max(d$dose))
    p <- predict(f, data.frame(dose = grid), xref = grid[1], expo = FALSE)
    pj <- obj(dose = vec(grid), pred = vec(p$pred), se = vec((p$ci.ub - p$pred) / qnorm(0.975)))
  }
  do.call(obj, c(head, list(ok = "true", coef = vec(b), vcov = vec(V), Psi = if (is.null(f$Psi)) NULL else vec(f$Psi),
    logLik = num(as.numeric(f$logLik)), converged = if (is.null(f$converged)) NULL else tolower(as.character(f$converged)),
    qtest = if (is.null(qt)) NULL else obj(Q = vec(qt$Q), df = vec(qt$df), p = vec(qt$pvalue)),
    wald = vec(wall), waldNonlin = if (is.null(wnl)) NULL else vec(wnl), gof = gj, pred = pj)))
}

GRID <- list()
for (m in c("linear", "quadratic", "rcs3", "rcs4", "rcs5")) {
  for (me in c("reml", "ml", "fixed", "mm")) GRID[[length(GRID) + 1]] <- list(m, "gl", "2stage", me)
  for (me in c("reml", "ml", "fixed")) GRID[[length(GRID) + 1]] <- list(m, "gl", "1stage", me)
}
for (m in c("linear", "rcs3", "rcs4")) for (pr in c("2stage", "1stage")) GRID[[length(GRID) + 1]] <- list(m, "h", pr, "reml")
for (m in c("linear", "rcs3")) for (pr in c("2stage", "1stage")) GRID[[length(GRID) + 1]] <- list(m, "indep", pr, "reml")

lines <- character()
for (ds in unique(corpus$dataset)) {
  d <- corpus[corpus$dataset == ds, c("id", "type", "dose", "cases", "n", "logrr", "se")]
  if (ds %in% names(MOD)) {   # attach the study-level covariate from the package data, by study id
    x <- get_ds(ds); cv <- tapply(as.numeric(x[[MOD[[ds]]]]), as.character(x$id), function(v) v[1])
    d$modv <- as.numeric(cv[as.character(d$id)])
  }
  bad <- unique(d$id[is.na(d$cases) | is.na(d$n)])
  d <- d[!d$id %in% bad, ]
  ids <- unique(d$id)
  if (length(ids) < 2) {
    lines <- c(lines, sprintf('{"dataset":"%s","k":%d,"excluded_studies":%d,"fits":[]}', ds, length(ids), length(bad))); next
  }
  d$id <- factor(d$id, levels = ids)
  fits <- vapply(GRID, function(g) fitone(d, g[[1]], g[[2]], g[[3]], g[[4]]), "")
  modj <- ""
  if (ds %in% names(MOD)) {
    modj <- sprintf(',"covariate":"%s","covariate_by_study":{%s}', MOD[[ds]],
                    paste(sprintf('"%s":%s', ids, num(d$modv[match(ids, d$id)])), collapse = ","))
    names(d)[names(d) == "modv"] <- MOD[[ds]]
    fits <- c(fits, vapply(c("linear", "rcs3"), function(mm) fitone(d, mm, "gl", "2stage", "reml", mod = MOD[[ds]]), ""))
  }
  lines <- c(lines, sprintf('{"dataset":"%s","k":%d,"excluded_studies":%d%s,"fits":[%s]}', ds, length(ids), length(bad), modj, paste(fits, collapse = ",")))
  cat(".")
}
dir.create(dirname(out), showWarnings = FALSE, recursive = TRUE)
writeLines(lines, out, useBytes = TRUE)
cat(sprintf("\ndosresmeta %s, mixmeta %s, rms %s, R %s: %d fits -> %s\n", packageVersion("dosresmeta"), packageVersion("mixmeta"),
            packageVersion("rms"), getRversion(), sum(lengths(regmatches(lines, gregexpr('"model":', lines)))), out))
