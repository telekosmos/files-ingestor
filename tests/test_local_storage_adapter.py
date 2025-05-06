import os
import tempfile
import unittest
from unittest.mock import Mock

from files_ingestor.adapters.repositories.local_storage import LocalStorageAdapter
from files_ingestor.domain.ports.logger_port import LoggerPort


class TestLocalStorageAdapter(unittest.TestCase):
    def setUp(self):
        """Set up test dependencies."""
        self.mock_logger = Mock(spec=LoggerPort)
        self.storage = LocalStorageAdapter(self.mock_logger)
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test files
        self.test_files = {
            'file1.pdf': 'test content 1',
            'file2.txt': 'test content 2',
            'subfolder/file3.pdf': 'test content 3',
            'subfolder/file4.txt': 'test content 4'
        }
        
        for path, content in self.test_files.items():
            full_path = os.path.join(self.temp_dir, path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(content)

    def tearDown(self):
        """Clean up test files."""
        for path in self.test_files:
            full_path = os.path.join(self.temp_dir, path)
            if os.path.exists(full_path):
                os.unlink(full_path)
        
        if os.path.exists(os.path.join(self.temp_dir, 'subfolder')):
            os.rmdir(os.path.join(self.temp_dir, 'subfolder'))
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    def test_is_cloud_url(self):
        """Test URL validation for local files."""
        self.assertTrue(self.storage.is_cloud_url('file:///path/to/file'))
        self.assertFalse(self.storage.is_cloud_url('s3://bucket/path'))
        self.assertFalse(self.storage.is_cloud_url('/absolute/path'))
        self.assertFalse(self.storage.is_cloud_url('relative/path'))

    def test_list_files_non_recursive(self):
        """Test listing files in a non-recursive manner."""
        url = f'file://{self.temp_dir}'
        files = self.storage.list_files(url, recursive=False)
        
        # Should only include files in root directory
        expected = {
            f'file://{os.path.join(self.temp_dir, "file1.pdf")}',
            f'file://{os.path.join(self.temp_dir, "file2.txt")}'
        }
        self.assertEqual(set(files), expected)

    def test_list_files_recursive(self):
        """Test listing files recursively."""
        url = f'file://{self.temp_dir}'
        files = self.storage.list_files(url, recursive=True)
        
        # Should include all files
        expected = {
            f'file://{os.path.join(self.temp_dir, path)}'
            for path in self.test_files
        }
        self.assertEqual(set(files), expected)

    def test_list_files_nonexistent_path(self):
        """Test listing files from a nonexistent path."""
        url = 'file:///nonexistent/path'
        with self.assertRaises(ValueError) as ctx:
            self.storage.list_files(url)
        self.assertIn('Local path not found', str(ctx.exception))

    def test_download_file_same_path(self):
        """Test downloading (linking) a file to the same path."""
        source = os.path.join(self.temp_dir, 'file1.pdf')
        url = f'file://{source}'
        
        # Try to download to same location
        result = self.storage.download_file(url, source)
        
        # Should return same path without creating link
        self.assertEqual(result, source)
        self.assertTrue(os.path.exists(source))
        
        # Verify content unchanged
        with open(source) as f:
            self.assertEqual(f.read(), 'test content 1')

    def test_download_file_new_path(self):
        """Test downloading (linking) a file to a new path."""
        source = os.path.join(self.temp_dir, 'file1.pdf')
        target = os.path.join(self.temp_dir, 'linked.pdf')
        url = f'file://{source}'
        
        # Download to new location
        result = self.storage.download_file(url, target)
        
        # Should create hard link
        self.assertEqual(result, target)
        self.assertTrue(os.path.exists(target))
        
        # Verify content
        with open(target) as f:
            self.assertEqual(f.read(), 'test content 1')
            
        # Clean up
        os.unlink(target)

    def test_download_file_nonexistent(self):
        """Test downloading a nonexistent file."""
        url = f'file://{self.temp_dir}/nonexistent.pdf'
        target = os.path.join(self.temp_dir, 'target.pdf')
        
        with self.assertRaises(ValueError) as ctx:
            self.storage.download_file(url, target)
        self.assertIn('Local file not found', str(ctx.exception))

    def test_invalid_url_raises_error(self):
        """Test that invalid URLs raise a ValueError."""
        invalid_urls = [
            's3://bucket/path',
            'https://example.com/file',
            '/absolute/path',
            'relative/path'
        ]
        
        for url in invalid_urls:
            with self.subTest(url=url):
                with self.assertRaises(ValueError) as ctx:
                    self.storage.list_files(url)
                self.assertIn('Invalid file URL', str(ctx.exception))
                
                with self.assertRaises(ValueError) as ctx:
                    self.storage.download_file(url, '/tmp/test.pdf')
                self.assertIn('Invalid file URL', str(ctx.exception))


if __name__ == '__main__':
    unittest.main() 