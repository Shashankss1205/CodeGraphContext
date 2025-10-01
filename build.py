from tree_sitter import Language, Parser


Language.build_library(
  # Output path for the .so/.dll file
  'build/my-languages.so',

  # List of language grammar repos
  [
    'vendor/tree-sitter-python',
    'vendor/tree-sitter-javascript'
  ]
)
