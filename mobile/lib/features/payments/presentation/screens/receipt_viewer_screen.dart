import 'dart:io';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_pdfview/flutter_pdfview.dart';
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart' show Share, XFile;

import '../../data/repositories/payment_repository.dart';

/// Full-screen PDF receipt viewer with share and download buttons.
class ReceiptViewerScreen extends StatefulWidget {
  final String paymentId;
  final PaymentRepository repository;
  const ReceiptViewerScreen({
    super.key,
    required this.paymentId,
    required this.repository,
  });

  @override
  State<ReceiptViewerScreen> createState() => _ReceiptViewerScreenState();
}

class _ReceiptViewerScreenState extends State<ReceiptViewerScreen> {
  Uint8List? _pdfBytes;
  String? _pdfPath;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadReceipt();
  }

  Future<void> _loadReceipt() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    final result = await widget.repository.getReceipt(widget.paymentId);
    result.fold(
      (failure) => setState(() {
        _error = failure.message;
        _loading = false;
      }),
      (bytes) async {
        _pdfBytes = bytes;
        // Write to temp file for PDFView
        final dir = await getTemporaryDirectory();
        final file = File(
            '${dir.path}/receipt_${widget.paymentId}.pdf');
        await file.writeAsBytes(bytes);
        setState(() {
          _pdfPath = file.path;
          _loading = false;
        });
      },
    );
  }

  Future<void> _shareReceipt() async {
    if (_pdfPath == null) return;
    await Share.shareXFiles(
      [XFile(_pdfPath!)],
      text: 'Payment Receipt',
    );
  }

  Future<void> _downloadReceipt() async {
    if (_pdfBytes == null) return;
    try {
      final dir = await getApplicationDocumentsDirectory();
      final file = File(
          '${dir.path}/receipt_${widget.paymentId}.pdf');
      await file.writeAsBytes(_pdfBytes!);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Saved to ${file.path}')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Failed to save receipt')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      key: const ValueKey('tc_s4_mob_receipt_viewer'),
      appBar: AppBar(
        title: const Text('Receipt'),
        actions: [
          IconButton(
            icon: const Icon(Icons.share_outlined),
            tooltip: 'Share',
            onPressed: _pdfPath != null ? _shareReceipt : null,
          ),
          IconButton(
            icon: const Icon(Icons.download_outlined),
            tooltip: 'Download',
            onPressed: _pdfBytes != null ? _downloadReceipt : null,
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.error_outline,
                          size: 48, color: theme.colorScheme.error),
                      const SizedBox(height: 12),
                      Text(_error!,
                          style:
                              TextStyle(color: theme.colorScheme.error)),
                      const SizedBox(height: 12),
                      FilledButton(
                        onPressed: _loadReceipt,
                        child: const Text('Retry'),
                      ),
                    ],
                  ),
                )
              : _pdfPath != null
                  ? PDFView(
                      filePath: _pdfPath!,
                      enableSwipe: true,
                      swipeHorizontal: false,
                      autoSpacing: true,
                      pageFling: true,
                    )
                  : const Center(child: Text('No receipt available')),
    );
  }
}
