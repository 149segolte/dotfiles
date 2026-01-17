-- [ Global configuration ]
vim.g.mapleader = ' '
vim.g.maplocalleader = ' '

vim.o.number = true -- Show line numbers
vim.o.relativenumber = true -- Show relative line numbers

vim.o.breakindent = true
vim.o.shiftround = true -- Round indent to multiple of shiftwidth
vim.o.softtabstop = 4 -- Number of spaces for a tab when editing
vim.o.shiftwidth = 4 -- Number of spaces for autoindent
vim.o.expandtab = true -- Use spaces instead of tabs

vim.o.ignorecase = true -- Ignore case in search
vim.o.smartcase = true

vim.o.list = true -- Show whitespace characters
vim.o.confirm = true
vim.o.showmode = false
vim.o.termguicolors = true -- Enable true colors
vim.o.inccommand = "split" -- Shows the effects of a command incrementally in the buffer

vim.o.colorcolumn = "80" -- Highlight column 80
vim.o.signcolumn = "yes" -- Always show sign column
vim.o.scrolloff = 4 -- Keep 8 lines above and below the cursor

vim.o.undofile = true -- Enable persistent undo
vim.o.swapfile = false -- Disable swap files

-- [ Custom keybinds ]
-- Allow qicker save and quit
vim.keymap.set('c', 'W', 'w', { desc = '(config): Save current file' })
vim.keymap.set('c', 'Q', 'q', { desc = '(config): Quit current window' })

-- Clear highlights on search when pressing <Esc> in normal mode
vim.keymap.set('n', '<Esc>', '<cmd>nohlsearch<CR>', { desc = '(config): Clear search highlights' })

-- Nicer copy/paste operations
vim.keymap.set('x', 'p', '"_dP', { desc = "(config): Paste without overwriting register" })
vim.keymap.set('x', 'y', '"+y', { desc = "(config): Yank to system clipboard" })

-- Toggle text wrapping
vim.keymap.set('n', '<leader>wr', '<cmd>set wrap!', { desc = '(config): Toggle text wrapping' })

-- Run lsp formatter
vim.keymap.set('n', '<leader>fi', vim.lsp.buf.format, { desc = '(config): LSP format immediately' })

-- Update plugins
vim.keymap.set('n', '<leader>lv', '<cmd>Lazy sync<CR>', { desc = '(config): Lazy.nvim sync' })

-- LSP keymaps
vim.keymap.set('n', 'grd', vim.lsp.buf.definition, { desc = '(config): Go to defination' })
vim.keymap.set('n', '<leader>q', vim.diagnostic.setloclist, { desc = '(config): Open diagnostic quickfix list' })

-- Keybinds to make split navigation easier. Use CTRL+<hjkl> to switch between windows
vim.keymap.set('n', '<C-h>', '<C-w><C-h>', { desc = '(config): Move focus to the left window' })
vim.keymap.set('n', '<C-l>', '<C-w><C-l>', { desc = '(config): Move focus to the right window' })
vim.keymap.set('n', '<C-j>', '<C-w><C-j>', { desc = '(config): Move focus to the lower window' })
vim.keymap.set('n', '<C-k>', '<C-w><C-k>', { desc = '(config): Move focus to the upper window' })

-- Toggle eol symbol in list mode
vim.o.listchars = "tab:» ,trail:·,nbsp:␣"

vim.keymap.set('n', '<leader>nl', function()
  if string.find(vim.o.listchars, "eol:") then
    vim.o.listchars = "tab:» ,trail:·,nbsp:␣"
  else
    vim.o.listchars = "tab:» ,trail:·,nbsp:␣,eol:⏎"
  end
end, { desc = '(config): Toggle "eol" symbol in list mode' })

-- Toggle format on save
vim.g.format_on_save = true

vim.keymap.set('n', '<leader>fg', function()
  vim.g.format_on_save = not vim.g.format_on_save
  print('format_on_save(global): ' .. tostring(vim.g.format_on_save))
end, { desc = '(config): Toggle "format_on_save" globally' })

vim.keymap.set('n', '<leader>fb', function()
  local output = ""
  if vim.g.format_on_save then
    if vim.b.format_on_save == nil then
      vim.b.format_on_save = not vim.g.format_on_save
    else
      vim.b.format_on_save = not vim.b.format_on_save
    end
    output = tostring(vim.b.format_on_save)
  else
    output = "disabled globally"
  end
  print('format_on_save(buffer): ' .. output)
end, { desc = '(config): Toggle "format_on_save" for current buffer' })

-- [ Autocommands ]
-- Highlight when yanking (copying) text
vim.api.nvim_create_autocmd('TextYankPost', {
  desc = '(config): Highlight when yanking (copying) text',
  group = vim.api.nvim_create_augroup('highlight-yank', { clear = true }),
  callback = function()
    vim.hl.on_yank()
  end,
})

-- FileType based augroup and autocmds
local ft_autocmds = 
-- Switch indentation based on filetypes
vim.api.nvim_create_autocmd("FileType", {
  desc = '(config): Switch indentation on filetypes',
  group = vim.api.nvim_create_augroup("filetype-indent", { clear = true }),
  callback = function(event)
    local lang_map = { lua = 2, template = 2 }
    local indent = lang_map[event.match] or 4
    vim.o.softtabstop = indent
    vim.o.shiftwidth = indent
  end,
})

-- [ Plugins ]
local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not (vim.uv or vim.loop).fs_stat(lazypath) then
  local lazyrepo = "https://github.com/folke/lazy.nvim.git"
  local out = vim.fn.system({ "git", "clone", "--filter=blob:none", "--branch=stable", lazyrepo, lazypath })
  if vim.v.shell_error ~= 0 then
    vim.api.nvim_echo({
      { "Failed to clone lazy.nvim:\n", "ErrorMsg" },
      { out, "WarningMsg" },
      { "\nPress any key to exit..." },
    }, true, {})
    vim.fn.getchar()
    os.exit(1)
  end
end
vim.opt.rtp:prepend(lazypath)

require("lazy").setup({
  spec = {

    {
      "folke/tokyonight.nvim",
      lazy = false,
      priority = 1000,
      opts = {
        transparent = true,
        dim_inactive = true,
      },
      config = function(_, opts)
        require('tokyonight').setup(opts)
        vim.cmd.colorscheme 'tokyonight-night'
      end,
    },

    { "folke/which-key.nvim", event = "VeryLazy", opts = {}},

    {
      'nvim-lualine/lualine.nvim',
      dependencies = { 'nvim-tree/nvim-web-devicons' },
      opts = {
        options = {
          theme = 'tokyonight',
          component_separators = '|',
          section_separators = '',
        },
        sections = {
          -- Defaults
          -- lualine_a = {'mode'},
          -- lualine_x = { 'encoding', 'fileformat', 'filetype' },
          lualine_a = {'mode', '#vim.fn.getbufinfo({buflisted = 1})'},
          lualine_x = { 'lsp_status', 'encoding', 'fileformat', 'filetype' },
        },
      },
    },

    { 'folke/todo-comments.nvim', event = 'VimEnter', dependencies = { 'nvim-lua/plenary.nvim' }, opts = { signs = false } },

    {
      'nvim-telescope/telescope.nvim',
      event = 'VimEnter',
      dependencies = {
        'nvim-lua/plenary.nvim',
        'nvim-tree/nvim-web-devicons',
        'nvim-telescope/telescope-ui-select.nvim',
        {
          'nvim-telescope/telescope-fzf-native.nvim',
          build = 'make',
          cond = function()
            return vim.fn.executable 'make' == 1
          end,
        },
      },
      config = function()
        require('telescope').setup {
          extensions = {
            ['ui-select'] = {
              require('telescope.themes').get_dropdown(),
            },
          },
        }

        -- Enable Telescope extensions if they are installed
        pcall(require('telescope').load_extension, 'fzf')
        pcall(require('telescope').load_extension, 'ui-select')

        local builtin = require 'telescope.builtin'
        vim.keymap.set('n', '<leader>sh', builtin.help_tags, { desc = '(telescope): Search help' })
        vim.keymap.set('n', '<leader>sk', builtin.keymaps, { desc = '(telescope): Search keymaps' })
        vim.keymap.set('n', '<leader>sf', builtin.find_files, { desc = '(telescope): Search files' })
        vim.keymap.set('n', '<leader>sw', builtin.grep_string, { desc = '(telescope): Search current word' })
        vim.keymap.set('n', '<leader>sg', builtin.live_grep, { desc = '(telescope): Search by grep' })
        vim.keymap.set('n', '<leader>sd', builtin.diagnostics, { desc = '(telescope): Search diagnostics' })
        vim.keymap.set('n', '<leader>sr', builtin.resume, { desc = '(telescope): Search resume' })
        vim.keymap.set('n', '<leader>s.', builtin.oldfiles, { desc = '(telescope): Search recent files ("." for repeat)' })
        vim.keymap.set('n', '<leader>/', builtin.current_buffer_fuzzy_find, { desc = '(telescope): Fuzzily search in current buffer' })
        vim.keymap.set('n', '<leader><leader>', builtin.buffers, { desc = '(telescope): Find existing buffers' })
        vim.keymap.set('n', '<leader>s/', function()
          builtin.live_grep {
            grep_open_files = true,
            prompt_title = 'Live Grep in Open Files',
          }
        end, { desc = '(telescope): Search in open files' })
      end,
    },

    {
      'nvim-treesitter/nvim-treesitter',
      lazy = false,
      build = ':TSUpdate',
      config = function()
        local languages = {
          'c',
          'cpp',
          'bash',
          'diff',
          'query',
          'vim',
          'vimdoc',
          'lua',
          'luadoc',
          'markdown',
          'markdown_inline',
          'python',
          'rust',
          'html',
          'javascript',
          'typescript',
          'tsx',
          'yaml',
        }
        require'nvim-treesitter'.install(languages)

        vim.api.nvim_create_autocmd('FileType', {
          pattern = languages,
          group = vim.api.nvim_create_augroup("treesitter-features", { clear = true }),
          callback = function()
            -- syntax highlighting, provided by Neovim
            vim.treesitter.start()
            -- folds, provided by Neovim
            -- vim.wo.foldexpr = 'v:lua.vim.treesitter.foldexpr()'
            -- vim.wo.foldmethod = 'expr'
            -- indentation, provided by nvim-treesitter
            -- vim.bo.indentexpr = "v:lua.require'nvim-treesitter'.indentexpr()"
          end,
        })
      end
    },

  },
})
