-- CreateTable
CREATE TABLE "Audit" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "url" TEXT NOT NULL,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "reportJson" TEXT NOT NULL
);

-- CreateIndex
CREATE INDEX "Audit_url_createdAt_idx" ON "Audit"("url", "createdAt");
