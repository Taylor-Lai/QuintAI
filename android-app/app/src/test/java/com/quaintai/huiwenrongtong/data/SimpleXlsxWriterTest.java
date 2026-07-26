package com.quaintai.huiwenrongtong.data;

import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.Arrays;
import java.util.zip.ZipFile;
import org.junit.Test;

public class SimpleXlsxWriterTest {
    @Test
    public void writesValidMinimalWorkbookWithEscapedHeaders() throws Exception {
        File target = Files.createTempFile("zhihui-template", ".xlsx").toFile();
        try {
            SimpleXlsxWriter.INSTANCE.write(target, Arrays.asList("合同编号", "甲方 & 乙方", "金额<元>"));
            try (ZipFile zip = new ZipFile(target)) {
                assertNotNull(zip.getEntry("[Content_Types].xml"));
                assertNotNull(zip.getEntry("xl/workbook.xml"));
                assertNotNull(zip.getEntry("xl/worksheets/sheet1.xml"));
                String sheet = new String(zip.getInputStream(zip.getEntry("xl/worksheets/sheet1.xml")).readAllBytes(), StandardCharsets.UTF_8);
                assertTrue(sheet.contains("合同编号"));
                assertTrue(sheet.contains("甲方 &amp; 乙方"));
                assertTrue(sheet.contains("金额&lt;元&gt;"));
            }
        } finally {
            target.delete();
        }
    }
}
