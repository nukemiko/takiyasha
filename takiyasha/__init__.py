VERSION: str = '0.2.0'
SUPPORTED_FORMATS_PATTERNS: dict[str, list[str]] = {
    'NCM': ['*.ncm'],
    'QMC': ['*.qmc[023468]', '*.qmcflac', '*.qmcogg',
            '*.tkm',
            '*.mflac', '*.mflac[0]', '*.mgg', '*.mgg[01l]',
            '*.bkcmp3', '*.bkcm4a', '*.bkcflac', '*.bkcwav', '*.bkcape', '*.bkcogg', '*.bkcwma']
}
